# backend/app/services/azure_di_service.py
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.formrecognizer import DocumentAnalysisClient
from app.core.config import settings

async def analyze_pdf(pdf_path: Path, locale: Optional[str] = "en-US") -> Dict[str, Any]:
    """
    Analyzes a single PDF file using Document Intelligence in an async manner.
    Args:
        pdf_path: The Path object pointing to the PDF file.
        locale: The locale of the document (e.g., "en-US").
    Returns:
        A dictionary containing the analysis result.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    print(f"Analyzing document: {pdf_path}")
    
    client = DocumentAnalysisClient(
        settings.DI_ENDPOINT, 
        AzureKeyCredential(settings.DI_KEY)
    )

    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        # begin_analyze_document is a sync method. We run it in a thread pool
        # to avoid blocking the asyncio event loop.
        poller = await asyncio.to_thread(
            client.begin_analyze_document,
            "prebuilt-document",
            pdf_data,
            locale=locale,
        )
        
        # result() is a sync method to wait for the poller to complete.
        result = await asyncio.to_thread(poller.result)

        # Convert the AnalyzeResult to a dictionary for JSON serialization
        return result.to_dict()

    except HttpResponseError as e:
        error_message = f"Azure service error during analysis of {pdf_path}: Status code {getattr(e.response, 'status_code', 'n/a')}"
        try:
            # Attempt to get more detailed error info from response
            error_content = e.response.text()
            error_message += f"\nDetails: {error_content}"
        except Exception:
            pass
        print(error_message)
        raise  # Re-raise the exception to be handled by the caller
    except Exception as e:
        print(f"An unexpected error occurred during PDF analysis for {pdf_path}: {e}")
        raise
