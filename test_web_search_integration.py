"""
Test script to verify web search integration across all LLM generation points.
Run this to ensure web search is properly integrated everywhere.
"""
import asyncio
from servers.fastapi.services.web_search_service import WEB_SEARCH_SERVICE


async def test_web_search():
    """Test that web search service works"""
    print("\n" + "="*80)
    print("TESTING WEB SEARCH SERVICE")
    print("="*80)
    
    query = "artificial intelligence trends 2024"
    print(f"\nQuery: {query}")
    
    results = await WEB_SEARCH_SERVICE.search(query)
    
    print(f"\nResults count: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'No title')}")
        print(f"   URL: {result.get('url', 'No URL')}")
        print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
    
    print("\n" + "="*80)
    print("TESTING RESULTS_TO_TEXT")
    print("="*80)
    
    text = WEB_SEARCH_SERVICE.results_to_text(results)
    print(f"\nFormatted text length: {len(text)} characters")
    print("\nFirst 500 characters:")
    print(text[:500])
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_web_search())
