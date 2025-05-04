from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
import ast
import re

class QueryRequest(BaseModel):
    query: str = Field(..., description="The user's natural language query for assessments.", min_length=1)

class RecommendedAssessment(BaseModel):
    url: Optional[str] = None
    adaptive_support: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    remote_support: Optional[str] = None
    test_type: Optional[Union[List[str], str]] = Field(default_factory=list)

class RecommendResponse(BaseModel):
    recommended_assessments: List[RecommendedAssessment]

class AssessmentSearchCriteria(BaseModel):
    job_role: Optional[str] = Field(None, description="The primary job role or title mentioned (e.g., 'Software Engineer', 'Sales Manager').")
    candidate_level: Optional[str] = Field(None, description="The seniority or experience level (e.g., 'entry-level', 'senior', 'manager').")
    key_skills_or_concepts: Optional[List[str]] = Field(None, description="List of essential skills, knowledge areas, or job responsibilities (e.g., ['Python', 'data analysis', 'customer interaction']).")
   

def parse_test_type(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str) or not value.strip():
        return []
    cleaned_value = value.strip()
    for delimiter in [',', ';', '|']:
        if delimiter in cleaned_value:
            parts = [item.strip() for item in cleaned_value.split(delimiter)]
            result = [part for part in parts if part]
            if result:
                return result
    try:
        parsed = ast.literal_eval(cleaned_value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        elif isinstance(parsed, (str, int, float)):
            item = str(parsed).strip()
            return [item] if item else []
    except (ValueError, SyntaxError, TypeError):
        pass
    return [cleaned_value]