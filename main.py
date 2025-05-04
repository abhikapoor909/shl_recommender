import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from services import initialize_components
    from api import router
except ImportError as e:
    sys.exit("Critical import error during startup.")
except Exception as e:
    sys.exit("Unexpected critical error during imports.")

app = FastAPI(
    title="Assessment Recommendation API",
    description="API to recommend job assessments based on natural language queries.",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    try:
        (
            initialized_df,
            initialized_retriever,
            initialized_chain,
            initialized_llm,
            initialized_embedding_model
        ) = initialize_components()

        app.state.dataframe = initialized_df
        app.state.retriever = initialized_retriever
        app.state.structured_chain = initialized_chain
        app.state.llm = initialized_llm
        app.state.embedding_model = initialized_embedding_model

    except Exception as e:
        app.state.dataframe = None
        app.state.retriever = None
        app.state.structured_chain = None
        app.state.llm = None
        app.state.embedding_model = None

@app.on_event("shutdown")
async def shutdown_event():
    pass

@app.get("/")
async def read_root():
    return {"message": "Welcome to the SHL Assessment Recommender API. Use /docs for documentation."}