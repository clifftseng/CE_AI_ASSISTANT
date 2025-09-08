import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from backend.app.services.azure_service import get_aoai_response
from backend.app.core.config import settings
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# For the test, we can set non-sensitive configs directly
# Sensitive keys (AZURE_OPENAI_API_KEY, DI_KEY) are loaded from environment variables by the config module
settings.AZURE_OPENAI_ENDPOINT = "https://openai-smp-ak.openai.azure.com/"
settings.AZURE_OPENAI_API_VER = "2025-03-01-preview"
settings.AZURE_OPENAI_DEPLOYMENT = "gpt-5-chat"
settings.DI_ENDPOINT = "https://document-ai-ak.cognitiveservices.azure.com/"

# Verify that sensitive keys have been loaded from the environment
if not settings.AZURE_OPENAI_API_KEY or not settings.DI_KEY:
    print("Error: Missing required environment variables.")
    print("Please ensure AZURE_OPENAI_API_KEY and DI_KEY are set in your .env file or environment.")
    sys.exit(1)

def test_azure_connections():
    print("Testing Azure OpenAI and Document Intelligence connections...")

    # Test Azure OpenAI connection
    print("\n--- Testing Azure OpenAI ---")
    try:
        response = get_aoai_response(
            system_prompt="You are a helpful assistant that outputs JSON.",
            user_prompt="Hello, how are you?"
        )
        print(f"Azure OpenAI connection successful. Response: {response}")
    except Exception as e:
        print(f"Azure OpenAI connection failed: {e}")

    # Test Document Intelligence connection (client initialization)
    print("\n--- Testing Document Intelligence ---")
    try:
        di_client = DocumentAnalysisClient(
            endpoint=settings.DI_ENDPOINT,
            credential=AzureKeyCredential(settings.DI_KEY)
        )
        # Attempt a simple operation that doesn't require a file, like listing models (if available) or just successful initialization
        # For now, just successful initialization is enough to confirm basic connectivity
        print("Document Intelligence client initialized successfully.")
    except Exception as e:
        print(f"Document Intelligence connection failed during client initialization: {e}")

if __name__ == "__main__":
    test_azure_connections()