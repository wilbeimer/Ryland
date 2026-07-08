import os
from googleapiclient.discovery import build


def search_youtube(query: str, max_results: int = 2) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

    response = (
        youtube.search()
        .list(
            q=query,
            part="snippet",
            maxResults=max_results,
            type="video",
            relevanceLanguage="en",
            safeSearch="strict",
        )
        .execute()
    )

    results = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        results.append(
            {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "type": "video",
                "description": item["snippet"]["description"],
                "channel": item["snippet"]["channelTitle"],
            }
        )

    return results
