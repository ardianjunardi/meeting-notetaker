import httpx
from app.config import settings


async def summarize_transcript(meeting_title: str, transcript: str) -> dict:
    """
    Send transcript to lite LLM (OpenAI-compatible API) and return structured minutes.
    Returns dict with keys: summary, action_items, pending_questions
    """
    prompt = f"""Analyze the following meeting transcript and produce:
1. A concise summary of the discussion (2-3 paragraphs)
2. Action items with assignees (if mentioned)
3. Pending questions or unresolved topics

Format your response as a JSON object with keys: "summary", "action_items" (array of {{"task": "...", "assignee": "...", "deadline": "..."}}), "pending_questions" (array of strings).

Meeting Title: {meeting_title}

Transcript:
{transcript}"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.llm_endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional meeting assistant. Always respond with valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )

            if response.status_code != 200:
                return _fallback_summary(transcript)

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Try to parse JSON from response
            import json

            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                # Remove optional "json" language tag
                if content.startswith("json"):
                    content = content[4:].strip()

            try:
                result = json.loads(content)
                return {
                    "summary": result.get("summary", ""),
                    "action_items": json.dumps(result.get("action_items", [])),
                    "pending_questions": json.dumps(result.get("pending_questions", [])),
                }
            except json.JSONDecodeError:
                return _fallback_summary(transcript)

    except Exception:
        return _fallback_summary(transcript)


def _fallback_summary(transcript: str) -> dict:
    """Return raw transcript as summary when LLM is unavailable."""
    import json

    return {
        "summary": f"(LLM unavailable - raw transcript saved)\n\n{transcript[:500]}...",
        "action_items": json.dumps([]),
        "pending_questions": json.dumps([]),
    }
