import streamlit as st
import requests
from typing import List, Dict, Any, Optional

API_BASE_URL = "https://shl-recommender-5.onrender.com"
RECOMMEND_ENDPOINT = f"{API_BASE_URL}/recommend"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

def check_backend_health() -> Dict[str, Any]:
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"status": "unreachable", "error": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"status": "unreachable", "error": "Could not connect to backend"}
    except requests.exceptions.RequestException as e:
        error_detail = f"Error: {e}"
        if e.response is not None:
            try:
                backend_error = e.response.json().get("detail", e.response.text)
                error_detail += f" | Backend Response: {backend_error}"
            except Exception:
                error_detail += f" | Backend Response: {e.response.text}"
        return {"status": "error", "error": error_detail}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}

def get_recommendations_from_api(query: str) -> Optional[List[Dict[str, Any]]]:
    payload = {"query": query}
    try:
        response = requests.post(RECOMMEND_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("recommended_assessments")
    except requests.exceptions.Timeout:
        st.error("Error: The request to the backend timed out. Please try again later.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Error: Could not connect to the backend API.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching recommendations: {e}")
        try:
            if e.response is not None:
                error_detail = e.response.json().get("detail", e.response.text)
                st.error(f"Backend Error Detail: {error_detail}")
        except Exception:
            st.error("Could not parse detailed error message from the backend.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def display_recommendations(recommendations: List[Dict[str, Any]]):
    if not recommendations:
        st.info("No recommendations found for your query.")
        return

    st.subheader(f"Top {len(recommendations)} Recommendations:")
    for i, rec in enumerate(recommendations):
        title = rec.get('assessment_name', f"Recommendation {i+1}")
        if not title:
            title = f"Recommendation {i+1}"

        with st.expander(f"**{i+1}. {title}**"):
            if rec.get('description'):
                st.write(f"**Description:** {rec['description']}")
            else:
                st.write("_No description provided._")

            if rec.get('url'):
                url = rec['url']
                if url.startswith(('http://', 'https://')):
                    st.markdown(f"**URL:** [{url}]({url})")
                else:
                    st.write(f"**URL (relative/other):** {url}")

            details = []
            if rec.get('duration') is not None:
                details.append(f"**Duration:** {rec['duration']} mins")
            if rec.get('test_type'):
                test_types = rec['test_type']
                if isinstance(test_types, list):
                    details.append(f"**Test Type(s):** {', '.join(filter(None, test_types))}")
                else:
                    details.append(f"**Test Type(s):** {test_types}")
            if rec.get('adaptive_support') is not None:
                details.append(f"**Adaptive Support:** {'Yes' if rec['adaptive_support'] else 'No'}")
            if rec.get('remote_support') is not None:
                details.append(f"**Remote Support:** {'Yes' if rec['remote_support'] else 'No'}")

            if details:
                st.write(" | ".join(details))
            elif not rec.get('description') and not rec.get('url'):
                st.write("_No further details provided._")

st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")
st.title("🤖 SHL Assessment Recommender")
st.markdown("Enter your requirements below to find relevant SHL assessments based on your criteria.")

st.sidebar.subheader("Backend Status")
health_status = check_backend_health()
status = health_status.get('status', 'unknown').lower()

if status == "healthy":
    st.sidebar.markdown("**Status:** <span style='color:green;'>HEALTHY</span>", unsafe_allow_html=True)
    details = health_status.get("details")
    if details:
        st.sidebar.success(f"Details: {details}")
elif status == "unhealthy":
    st.sidebar.markdown("**Status:** <span style='color:orange;'>UNHEALTHY</span>", unsafe_allow_html=True)
    details = health_status.get("details")
    if details:
        st.sidebar.warning(f"Details: {details}")
    if health_status.get("error"):
        st.sidebar.error(f"Error: {health_status['error']}")
else:
    st.sidebar.markdown(f"**Status:** <span style='color:red;'>{status.upper()}</span>", unsafe_allow_html=True)
    if health_status.get("error"):
        st.sidebar.error(f"Error: {health_status['error']}")

st.sidebar.markdown("---")
st.sidebar.info(f"Using API Endpoint: `{API_BASE_URL}`")

query = st.text_area(
    "Enter your assessment query:",
    height=150,
    placeholder="Example: I need an unsupervised assessment for graduate-level candidates focusing on numerical reasoning and logical thinking, suitable for remote proctoring."
)

if st.button("Find Recommendations"):
    if not query or query.isspace():
        st.warning("Please enter a query describing your assessment needs.")
    else:
        with st.spinner("🧠 Analyzing query and searching for assessments..."):
            recommendations = get_recommendations_from_api(query)
        if recommendations is not None:
            display_recommendations(recommendations)

st.markdown("---")
st.caption("Powered by FastAPI, Langchain, and Streamlit.")