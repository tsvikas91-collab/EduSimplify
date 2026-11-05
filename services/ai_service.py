import os
import requests

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
DEFAULT_WATSONX_URL = "https://us-south.ml.cloud.ibm.com"

def granite_is_configured():
    return bool(
        os.getenv("IBM_CLOUD_API_KEY")
        and os.getenv("WATSONX_PROJECT_ID")
        and os.getenv("WATSONX_MODEL_ID")
    )

def get_iam_token(api_key):
    response = requests.post(
        IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]

def headers(extra=None):
    result = {}
    if extra:
        result.update(extra)
    return result

def build_prompt(content, level, task):
    level_guidance = {
        "Beginner": "Use very simple everyday English. Explain technical words. Assume no prior knowledge.",
        "Intermediate": "Use clear student-friendly language. Assume basic subject knowledge and explain important technical terms.",
        "Advanced": "Keep technical accuracy and detail. Explain relationships, mechanisms, and important terminology.",
        "Expert": "Use precise technical language, deeper reasoning, and discipline-specific terminology. Do not oversimplify.",
    }
    task_guidance = {
        "Simplify": "Rewrite the material in an easier-to-understand form. Preserve all important facts and concepts.",
        "Summarize": "Create a concise, well-organized summary of the material.",
        "Key points": "Extract the most important points as clear bullet points. Keep definitions and formulas when present.",
        "Examples": "Explain the concepts and provide useful practical or real-world examples. Do not invent facts about the source.",
        "Quiz": "Create 5 questions based only on the supplied material. Include a mix of short-answer and multiple-choice questions, then provide an answer key.",
    }
    return f"""
You are EduSimplify, a careful academic learning assistant.
Audience level: {level}.
Writing guidance: {level_guidance[level]}
Requested task: {task_guidance[task]}

Rules:
- Use only the supplied course material for source-specific claims.
- Do not invent definitions, formulas, facts, or citations.
- If information is missing or unclear, say so.
- Preserve the original meaning and important technical terms.
- Use headings and readable formatting.
- Make the answer educational and respectful.

COURSE MATERIAL:
{content}
"""

def simplify_with_granite(content, level, task):
    api_key = os.getenv("IBM_CLOUD_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    model_id = os.getenv("WATSONX_MODEL_ID")
    if not (api_key and project_id and model_id):
        return demo_response(content, level, task)

    token = get_iam_token(api_key)
    base_url = os.getenv("WATSONX_URL", DEFAULT_WATSONX_URL).rstrip("/")
    version = os.getenv("WATSONX_API_VERSION", "2023-05-29")
    url = f"{base_url}/ml/v1/text/chat?version={version}"
    payload = {
        "model_id": model_id,
        "project_id": project_id,
        "messages": [
            {"role": "system", "content": "You are EduSimplify, an accurate academic learning assistant."},
            {"role": "user", "content": build_prompt(content, level, task)}
        ],
        "temperature": 0.3,
        "max_tokens": 1800
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json=payload,
        timeout=120
    )
    if not response.ok:
        raise RuntimeError(f"IBM watsonx.ai request failed ({response.status_code}): {response.text[:700]}")
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("IBM returned an unexpected response format. Check your model ID and API settings.")

def demo_response(content, level, task):
    preview = content[:1800].strip()
    notice = (
        "DEMO MODE — IBM Granite is not connected yet. Add your IBM credentials to the .env file "
        "to enable real AI responses.\n\n"
    )
    if task == "Quiz":
        body = (
            "Sample quiz based on the uploaded material:\n\n"
            "1. What is the main topic discussed in the material?\n"
            "2. Explain one important concept from the material.\n"
            "3. Which key term is used in the material?\n"
            "4. Give one example mentioned in the material.\n"
            "5. What is the main conclusion?\n\n"
            "Answer guide: Review the corresponding sections in your source material. "
            "Connect IBM Granite to generate content-specific questions and answers."
        )
    elif task == "Key points":
        body = "Key points to review:\n\n" + "\n".join(
            f"• {line.strip()}" for line in preview.splitlines() if line.strip()
        )
    elif task == "Examples":
        body = (
            f"Learning level: {level}\n\n"
            "Source material preview:\n" + preview +
            "\n\nExample generation will be powered by IBM Granite after credentials are configured."
        )
    elif task == "Summarize":
        body = "Source material preview:\n\n" + preview + (
            "\n\nConnect IBM Granite to generate a concise, accurate summary."
        )
    else:
        body = (
            f"Learning level: {level}\n\n"
            "Here is the extracted course content:\n\n" + preview +
            "\n\nConnect IBM Granite to rewrite this content in genuinely simplified language."
        )
    return notice + body
