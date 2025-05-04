from fastapi import APIRouter, HTTPException, Request
from models import QueryRequest, RecommendResponse, RecommendedAssessment
from services import get_recommendations
from typing import List
import os

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def recommend_assessments(request: Request, query_request: QueryRequest):
    try:
        df_ref = getattr(request.app.state, 'dataframe', None)
        retriever_ref = getattr(request.app.state, 'retriever', None)
        chain_ref = getattr(request.app.state, 'structured_chain', None)

        if df_ref is None or retriever_ref is None or chain_ref is None:
            raise HTTPException(status_code=503, detail="Service not ready, components not initialized.")

        recommendations: List[RecommendedAssessment] = await get_recommendations(
            query=query_request.query,
            df_ref=df_ref,
            retriever_ref=retriever_ref,
            structured_chain_ref=chain_ref
        )
        return RecommendResponse(recommended_assessments=recommendations)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@router.get("/health")
async def health_check(request: Request):
    df_state = getattr(request.app.state, 'dataframe', None)
    retriever_state = getattr(request.app.state, 'retriever', None)
    chain_state = getattr(request.app.state, 'structured_chain', None)

    healthy = True
    details = []

    if retriever_state is None:
        healthy = False
        details.append("Retriever not initialized")
    if chain_state is None:
        healthy = False
        details.append("Analysis chain not initialized")
    if df_state is None or df_state.empty:
        healthy = False
        details.append("Dataframe not loaded or empty")

    response_body = {"status": "healthy" if healthy else "unhealthy"}
    if not healthy:
        response_body["details"] = ", ".join(details)

    return response_body