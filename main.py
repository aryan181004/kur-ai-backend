from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse

app = FastAPI()

# Enable CORS for localhost:3000 (React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    search_query: str
    
@app.post("/api/enrich")
async def get_wikipedia_summary(request: SearchRequest):
    search_query = request.search_query
    encoded_search_query = urllib.parse.quote_plus(search_query)

    # Fetch summary from Wikipedia API
    response = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_search_query}')
    print(f"Fetching from: {response.url}")  # Log the URL
    print(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {data}")  # Log the full data
        
        summary = data.get('extract', "Summary not found.")
        links = [data.get('content_urls', {}).get('desktop', {}).get('page', "No URL found")]
        image_url = data.get('thumbnail', {}).get('source', None)

        return {
            "summary": summary,
            "links": links,
            "image": image_url
        }
    else:
        # If not found, try to search with OpenSearch for better results
        search_url = f'https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_search_query}&limit=1&namespace=0&format=json'
        search_response = requests.get(search_url)
        search_data = search_response.json()
        print(f"OpenSearch response data: {search_data}")

        if not search_data[1]:
            raise HTTPException(status_code=404, detail="No results found.")

        # Get the first search result and fetch its summary
        redirect_page_url = search_data[3][0]
        page_title = redirect_page_url.split("/")[-1]

        response = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}')
        print(f"Fetching from: {response.url}")  # Log the URL
        print(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")  # Log the full data

            summary = data.get('extract', "Summary not found.")
            links = [data.get('content_urls', {}).get('desktop', {}).get('page', "No URL found")]
            image_url = data.get('thumbnail', {}).get('source', None)

            return {
                "summary": summary,
                "links": links,
                "image": image_url
            }
        else:
            raise HTTPException(status_code=404, detail="No data found.")
