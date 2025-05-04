from models import AssessmentSearchCriteria
import config

def construct_search_query_from_structured(criteria: AssessmentSearchCriteria) -> str:
    query_parts = []

    if criteria.job_role:
        query_parts.extend([criteria.job_role] * config.JOB_ROLE_REPETITION)

    if criteria.candidate_level:
        query_parts.append(criteria.candidate_level * 2)

    if criteria.key_skills_or_concepts:
        query_parts.extend(criteria.key_skills_or_concepts * 3)

    if not query_parts:
        return "job assessment"

    seen = set()
    final_query_parts = []
    for part in query_parts:
        part_lower = part.lower()
        if part_lower not in seen:
            final_query_parts.append(part)
            seen.add(part_lower)

    search_query = " ".join(final_query_parts)
    return f"assessment for {search_query}"