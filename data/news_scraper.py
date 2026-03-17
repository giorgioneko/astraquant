import requests
import os
from dotenv import load_dotenv

load_dotenv()

class NewsFetcher:
    def __init__(self):
        # We can use NewsAPI or similar. Using a free tier or placeholder for now.
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_recent_news(self, query: str, days_back: int = 1) -> list:
        """
        Fetches recent news articles for a given query (e.g., 'Apple', 'Bitcoin').
        """
        if not self.api_key:
            print("WARNING: NEWS_API_KEY not found in environment. Returning mock data.")
            return [
                {"title": f"{query} sees unexpected growth this quarter.", "source": "MockNews"},
                {"title": f"Regulatory concerns hit {query} market.", "source": "MockNews"}
            ]

        print(f"Fetching news for {query}...")
        try:
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "apiKey": self.api_key,
                "pageSize": 5
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_recent_news("Bitcoin", days_back=1)
    for n in news:
        print(f"- {n.get('title')}")
