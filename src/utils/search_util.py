from src.config import settings
from tavily import TavilyClient


async def search_with_tavily(
        query: str,
        top_n: int = 1,
):
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY,)
        response = client.search(
            query=query,
            include_images=True,
            max_results=top_n,
        )

        images = response.get("images", [])

        return {"images": images[:top_n]}
    except Exception as e:
        raise e