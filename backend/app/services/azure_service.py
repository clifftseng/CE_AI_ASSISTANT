
import os
import json
from typing import Optional
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from ..core.config import settings

def analyze_document_from_path(pdf_path: str, locale: Optional[str] = "en-US") -> dict:
    """
    Analyzes a PDF file from a path using Document Intelligence.
    """
    print(f"[DEBUG] DI Endpoint: {settings.DI_ENDPOINT}", flush=True)
    print(f"[DEBUG] DI Key (masked): {settings.DI_KEY[:5] if settings.DI_KEY else 'N/A'}...", flush=True)
    client = DocumentAnalysisClient(settings.DI_ENDPOINT, AzureKeyCredential(settings.DI_KEY))
    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-document", f.read(), locale=locale)
    result = poller.result()
    return result.to_dict()

def get_aoai_response(system_prompt: str, user_prompt: str) -> dict:
    """
    Calls the Azure OpenAI API and returns the parsed JSON response.
    """
    print(f"[DEBUG] AOAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT}", flush=True)
    print(f"[DEBUG] AOAI Key (masked): {settings.AZURE_OPENAI_API_KEY[:5] if settings.AZURE_OPENAI_API_KEY else 'N/A'}...", flush=True)
    print(f"[DEBUG] AOAI API Version: {settings.AZURE_OPENAI_API_VER}", flush=True)
    print(f"[DEBUG] AOAI Deployment: {settings.AZURE_OPENAI_DEPLOYMENT}", flush=True)
    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VER,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        timeout=60.0 # Add timeout here
    )

    raw_text = response.choices[0].message.content or ""
    if not raw_text.strip():
        raise ValueError("AOAI response is empty.")

    try:
        # The response should be a JSON string, as requested.
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # If it fails, try to find a JSON block in the text
        match = json.loads(raw_text[raw_text.find("{") : raw_text.rfind("}") + 1])
        if match:
            return match
        raise ValueError(f"Failed to decode JSON from AOAI response: {raw_text}")



