# Website Project

# CE_AI_ASSISTANT

AI-powered assistant with a **FastAPI** backend and a **Vite + React + TypeScript** frontend.  
Containerized with **Docker Compose** and integrates with Azure services (e.g., Azure OpenAI, Azure Form Recognizer).

---

## Project Structure
backend/ # FastAPI application
frontend/ # Vite + React + TypeScript app
nginx/ # Nginx config for reverse proxy (if used)
docker-compose.yml # Multi-service local/dev setup

---

## Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (optional but recommended)
- Azure credentials stored in environment variables (do NOT hardcode secrets)

---

## Environment Variables

Create a local `.env` (do not commit it). Example:
```
Backend

FRONTEND_ORIGIN=http://localhost:8080

DATA_DIR=.data

Azure (examples; do not share real values)

AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/

AZURE_OPENAI_KEY=your_key_here
FORM_RECOGNIZER_ENDPOINT=https://xxx.cognitiveservices.azure.com/

FORM_RECOGNIZER_KEY=your_key_here
```

---

## Run Locally (without Docker)

### Backend
```bash
# 1) create venv & install deps
python -m venv .venv
# Windows PowerShell:
. .\.venv\Scripts\Activate.ps1
# Windows CMD:
# .venv\Scripts\activate
pip install -r backend/requirements.txt

# 2) set env vars (PowerShell)
$env:FRONTEND_ORIGIN="http://localhost:8080"
$env:DATA_DIR=".data"

# 3) run FastAPI with a single worker (SSE requires 1 worker)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## Getting Started

### Running Backend Locally

1.  **Install Python dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r backend/requirements.txt
    ```
2.  **Set environment variables:**
    ```bash
    export FRONTEND_ORIGIN=http://localhost:8080
    export DATA_DIR=.data
    # On Windows, use 'set' instead of 'export':
    # set FRONTEND_ORIGIN=http://localhost:8080
    # set DATA_DIR=.data
    ```
3.  **Run the backend server:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
    ```
    *Important: Ensure you run with `--workers 1` for SSE to work correctly.*

### Running Frontend Locally

1.  **Install Node.js dependencies:**
    ```bash
    npm install   # or yarn / pnpm
    ```
2.  **Update Vite proxy configuration:**
    Open `frontend/vite.config.ts` and ensure the `server.proxy` section looks like this:
    ```typescript
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    }
    ```
3.  **Run the frontend development server:**
    ```bash
    npm run dev   # runs on http://localhost:8080
    ```

### Backend API Endpoints

- **`GET /api/health`**: Checks the health of the backend. Returns `{"status": "ok"}`.
- **`POST /api/value/upload`**: Uploads an Excel file and multiple PDF files.
  - **Request:** `multipart/form-data` with `excel_file` and `pdf_files`.
  - **Response:** `{"job_id": "..."}`
- **`GET /api/value/result/{job_id}`**: Retrieves the current status and result of a processing job.
  - **Response:** `{"status": "...", "download_url": "...", "query_fields": [...], "query_targets": [...]}`
- **`GET /api/value/subscribe/{job_id}`**: Subscribes to Server-Sent Events (SSE) for real-time job progress updates.
  - **Events:**
    - `status`: Emitted periodically with processing messages.
    - `result`: Emitted when the job is successfully completed, includes `download_url`, `query_fields`, `query_targets`.
    - `error`: Emitted if an error occurs during processing.
- **`GET /api/download/{file_id}`**: Downloads the processed result file.

### Frontend (Value2.tsx) Integration Notes

To integrate with the backend, `frontend/src/pages/Value2.tsx` (or similar component handling value processing) should:

1.  **Upload Files:**
    -   Make a `POST` request to `/api/value/upload` with the selected Excel and PDF files.
    -   Extract the `job_id` from the response.

2.  **Subscribe to SSE for Progress Updates:**
    -   Construct the SSE URL: `const sseUrl = `/api/value/subscribe/${encodeURIComponent(result.job_id)}`;`
    -   Create an `EventSource` instance: `const es = new EventSource(sseUrl);`
    -   Add event listeners for `status`, `result`, and `error` events:
        ```typescript
        es.addEventListener('status', (event) => {
            const data = JSON.parse(event.data);
            // Append status messages to UI
            console.log('Status:', data.message);
        });

        es.addEventListener('result', (event) => {
            const data = JSON.parse(event.data);
            // Set download_url, query_fields, query_targets in UI state
            console.log('Result:', data);
            es.close(); // Close SSE connection once result is received
        });

        es.addEventListener('error', (event) => {
            const data = JSON.parse(event.data);
            // Display error message to user
            console.error('Error:', data);
            es.close(); // Close SSE connection on error
        });
        ```
    -   Ensure proper cleanup: The `EventSource` connection should be closed when the component unmounts or when the job is complete (e.g., in a `useEffect` cleanup function).
        ```typescript
        useEffect(() => {
            // ... SSE setup ...
            return () => {
                es.close(); // Cleanup on unmount
            };
        }, [jobId]); // Re-run effect if jobId changes
        ```
    -   Do not reset the selected files before submission; only clear old messages.
"# CE_AI_ASSISTANT"    # 建立一個簡單的 README.md
