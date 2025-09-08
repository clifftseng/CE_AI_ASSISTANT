# backend/app/services/aoai_core_service.py
import asyncio
import json
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI, AsyncAzureOpenAI
from app.core.config import settings

# Initialize the synchronous client for potential sync operations if needed
# client = AzureOpenAI(
#     azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
#     api_key=settings.AZURE_OPENAI_API_KEY,
#     api_version=settings.AZURE_OPENAI_API_VER,
# )

# Initialize the asynchronous client for FastAPI
async_client = AsyncAzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VER,
)

def extract_first_json_block(text: str) -> Optional[str]:
    """
    Tries to find the first complete JSON object block in a string.
    Returns None if no valid JSON object is found.
    """
    start = text.find("{")
    if start == -1:
        return None
    
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def build_user_payload(
    docs: List[Dict[str, Any]],
    pns: List[str],
    items: List[str],
    language: str = "zh-TW",
    return_source_excerpt: bool = True
) -> Dict[str, Any]:
    """Constructs the user payload for the LLM."""
    return {
        "docs": docs,
        "targets": {"pns": pns, "items": items},
        "options": {
            "suffix_map": {},
            "language": language,
            "return_source_excerpt": return_source_excerpt,
        },
        "excel_context": {},
    }

async def call_aoai_extractor(system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the AOAI chat completion API asynchronously and requests JSON output.
    """
    print("\nCalling AOAI API...")
    try:
        rsp = await async_client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = rsp.choices[0].message.content

        if not content:
            raise ValueError("Received an empty response from AOAI.")

        # Try to parse JSON directly
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("[WARNING] AOAI response was not valid JSON, attempting to extract from code block...")
            json_block = extract_first_json_block(content)
            if json_block:
                try:
                    return json.loads(json_block)
                except json.JSONDecodeError:
                    print("[ERROR] Content extracted from code block is still not valid JSON.")
                    raise ValueError(f"Could not parse LLM response: {content}")
            else:
                raise ValueError(f"No JSON block found in LLM response: {content}")

    except Exception as e:
        print(f"[ERROR] An error occurred while calling the AOAI API: {e}")
        # In a real app, you might want to raise a custom exception
        return {"error": str(e)}
