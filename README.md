# SHL Recommender System

This project involves scraping data from the SHL product catalog to provide personalizedtest recommendations based on individual assessments.

## Project Overview

The data is scraped from the [SHL Product Catalog](https://www.shl.com/products/product-catalog/), specifically focusing on individual test assessments. The project is designed to provide personalized recommendations through a web interface.

- **Frontend**: Deployed on Streamlit – [View App](https://shl-recommend.streamlit.app/)
- **Backend**: Deployed on Render 
  - [Health API](https://shl-recommender-ik0b.onrender.com/health)
  - [Recommendations API](https://shl-recommender-ik0b.onrender.com/recommend)

### Evaluation Report
Although I faced some challenges during evaluation, I made sure to extract the most relevant results. You can view the detailed evaluation report [here](https://drive.google.com/file/d/1YqNZPzVGglw37aZyGJaIB0qdvaOnFtgD/view?usp=drive_link).

## Key Challenges & Solutions

### 1. **Irrelevant Results from Cosine Similarity Search**
When I initially used cosine similarity to match the query with the vector database, irrelevant text was often returned. This happened because irrelevant parts of the query were still affecting the search results.

**Solution**: To address this, I utilized a Language Model (LLM) to refine the query. The LLM focused on the key aspects of the query, which significantly improved the relevance of the results when applied to the vector search.

### 2. **Memory Crashes During Deployment**
During deployment, memory crashes occurred due to the large embeddings required by the initial solution, which led to excessive package downloads and increased memory usage.

**Solution**: I switched to using Cohere embeddings, which were more efficient and reduced memory usage, allowing the application to run smoothly without causing crashes.

## Conclusion
This project aims to provide users with relevant health and test recommendations based on scraped data from SHL. Through iterative improvements in query handling and memory management, the system delivers more accurate results and has been successfully deployed.
