import pandas as pd
import re
from langchain.schema import Document
from langchain_community.embeddings import CohereEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any, Tuple
import config
from models import RecommendedAssessment, AssessmentSearchCriteria
from helpers import construct_search_query_from_structured

load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

df: Optional[pd.DataFrame] = None
vectorstore: Optional[FAISS] = None
retriever: Optional[Any] = None
structured_chain: Optional[Any] = None
embedding_model: Optional[CohereEmbeddings] = None
llm: Optional[ChatGroq] = None

def initialize_components() -> Tuple[pd.DataFrame, Any, Any, Any, CohereEmbeddings]:
    global df, vectorstore, retriever, structured_chain, embedding_model, llm

    local_df = None
    local_vectorstore = None
    local_retriever = None
    local_structured_chain = None
    local_embedding_model = None
    local_llm = None

    try:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found.")
        if not COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY not found.")

        csv_path = config.CSV_FILE_PATH
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        temp_df = pd.read_csv(csv_path)
        local_df = temp_df[config.EXPECTED_CSV_COLS].copy()
        for col in local_df.columns:
            if col == "Assessment Length":
                local_df[col] = local_df[col].apply(lambda x: int(re.search(r'\d+', str(x)).group(0)) if pd.notna(x) and re.search(r'\d+', str(x)) else None)
            else:
                local_df[col] = local_df[col].fillna('').astype(str)
        df = local_df

        docs = []
        for i, row in local_df.iterrows():
            content_parts = []
            for col in config.CONTENT_CSV_COLS:
                if col in row and pd.notna(row[col]) and str(row[col]).strip():
                    content_parts.append(f"{col}: {row[col]}")
            page_content = "\n".join(content_parts) if content_parts else f"Assessment details row index {i}"
            metadata = {"row_index": i}
            for csv_col in config.METADATA_CSV_COLS:
                meta_key = config.TARGET_FIELD_TO_METADATA_KEY.get(config.CSV_TO_JSON_MAP.get(csv_col))
                if meta_key:
                    value = row.get(csv_col)
                    metadata[meta_key] = None if pd.isna(value) else value
            docs.append(Document(page_content=page_content, metadata=metadata))
        if not docs:
            raise ValueError("Failed to create any documents for vector store.")

        local_embedding_model = CohereEmbeddings(
            cohere_api_key=COHERE_API_KEY,
            model=config.COHERE_EMBEDDING_MODEL_NAME,
            user_agent="langchain"
        )
        embedding_model = local_embedding_model

        local_vectorstore = FAISS.from_documents(docs, local_embedding_model)
        local_retriever = local_vectorstore.as_retriever(search_kwargs={'k': config.NUM_DOCS_TO_RETRIEVE})
        vectorstore = local_vectorstore
        retriever = local_retriever

        local_llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name=config.LLM_MODEL_NAME)
        llm = local_llm

        structured_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert query analyst specializing in job assessment matching. "
                "Analyze the user's request and extract the primary job role, candidate level, "
                "and key skills or concepts relevant to the role. "
                "Focus exclusively on these aspects. "
                "Ignore mentions of duration, test types, or preferences unless essential to job requirements. "
                "Use the provided JSON schema, filling only job_role, candidate_level, and key_skills_or_concepts."
            )),
            ("human", "Analyze the following user query:\n\nQuery: ```{original_query}```"),
        ])
        local_structured_chain = structured_prompt | local_llm.with_structured_output(AssessmentSearchCriteria)
        structured_chain = local_structured_chain

        return local_df, local_retriever, local_structured_chain, local_llm, local_embedding_model

    except Exception as e:
        df, vectorstore, retriever, structured_chain, embedding_model, llm = None, None, None, None, None, None
        raise e

async def get_recommendations(
    query: str,
    df_ref: pd.DataFrame,
    retriever_ref: Any,
    structured_chain_ref: Any
) -> List[RecommendedAssessment]:
    if retriever_ref is None or structured_chain_ref is None or df_ref is None or df_ref.empty:
        raise ValueError("Recommendation engine components are not valid.")

    final_search_query = query
    try:
        structured_result: Optional[AssessmentSearchCriteria] = await structured_chain_ref.ainvoke({"original_query": query})
        if structured_result and (structured_result.job_role or structured_result.candidate_level or structured_result.key_skills_or_concepts):
            final_search_query = construct_search_query_from_structured(structured_result)

        retrieved_docs = retriever_ref.get_relevant_documents(final_search_query)

        recommendations = []
        processed_indices = set()
        for doc in retrieved_docs:
            if len(recommendations) >= config.NUM_DOCS_TO_RETURN:
                break
            row_index = doc.metadata.get("row_index")
            if row_index is None:
                continue
            try:
                row_index = int(row_index)
            except (ValueError, TypeError):
                continue
            if row_index in processed_indices or row_index not in df_ref.index:
                continue
            processed_indices.add(row_index)
            assessment_data = {}
            for json_field in config.TARGET_JSON_FIELDS:
                metadata_key = config.TARGET_FIELD_TO_METADATA_KEY.get(json_field)
                if metadata_key:
                    assessment_data[json_field] = doc.metadata.get(metadata_key)
            try:
                recommendations.append(RecommendedAssessment(**assessment_data))
            except Exception:
                continue

        return recommendations

    except Exception as e:
        raise