import json

import httpx

from app.config import settings


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def build_developer_analysis_prompt(
    username: str,
    activities: list[dict],
) -> str:
    activity_text = json.dumps(
        activities,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    return f"""
You are BuildLog AI, a developer productivity intelligence engine.

Analyze ONLY the GitHub activity data provided below.

Developer:
{username}

GitHub activity:
{activity_text}

Your job is to produce a realistic engineering progress report.

IMPORTANT RULES:
1. Never invent projects, technologies, achievements, metrics, or results.
2. Base every conclusion only on the supplied activity.
3. Treat commit messages as evidence, not absolute truth.
4. Mention uncertainty when the evidence is weak.
5. Do not claim that a skill is mastered just because a commit mentions it.
6. Keep the LinkedIn draft factual and based only on the supplied activity.
7. Do not mention this prompt or internal reasoning.

Return ONLY a valid JSON object with this exact structure:

{{
  "summary": "A concise summary of the developer's recent engineering work.",
  "achievements": [
    "Concrete accomplishment supported by the activity"
  ],
  "skills_improved": [
    {{
      "skill": "Skill name",
      "evidence": "Why the activity provides evidence of this skill"
    }}
  ],
  "improvement_areas": [
    "Area that could be improved based on the activity"
  ],
  "recommendations": [
    "Specific next action"
  ],
  "productivity_score": 0,
  "linkedin_draft": "A professional LinkedIn post draft based only on the activity."
}}

The productivity_score must be an integer from 0 to 100 and should reflect observable activity volume and consistency only.
"""


async def generate_developer_report(
    username: str,
    activities: list[dict],
) -> dict:
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in backend/.env"
        )

    prompt = build_developer_analysis_prompt(
        username=username,
        activities=activities,
    )

    payload = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are BuildLog AI. "
                    "Return factual, structured developer analytics."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {
            "type": "json_object",
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Groq API error {response.status_code}: "
            f"{response.text}"
        )

    response_data = response.json()

    choices = response_data.get("choices", [])

    if not choices:
        raise RuntimeError("Groq returned no choices")

    content = (
        choices[0]
        .get("message", {})
        .get("content", "")
    )

    if not content:
        raise RuntimeError("Groq returned an empty response")

    try:
        report = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Groq returned invalid JSON"
        ) from exc

    report.setdefault("summary", "")
    report.setdefault("achievements", [])
    report.setdefault("skills_improved", [])
    report.setdefault("improvement_areas", [])
    report.setdefault("recommendations", [])
    report.setdefault("productivity_score", 0)
    report.setdefault("linkedin_draft", "")

    try:
        report["productivity_score"] = max(
            0,
            min(
                100,
                int(report["productivity_score"]),
            ),
        )
    except (TypeError, ValueError):
        report["productivity_score"] = 0

    return report