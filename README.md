# Website Project

## 嚴格的驗收條件

- 使用 `uvicorn app.main:app --reload --port 8000`（單一 worker）。
- 前端在 `http://localhost:8080`。
- 上傳 1 個 `.xlsx` + ≥1 個 `.pdf`。
- 在瀏覽器 DevTools → Network 看到 `GET /api/value/subscribe/<job_id>` 型別 `EventStream`。
- 在 5 秒內收到第一則 `status` 事件，整個過程至少 2 則 `status`，最後 1 則 `result`（含 `download_url`、`query_fields`、`query_targets`）。

## Directory Structure

- `aoai_method/`: Contains the Azure OpenAI method for document processing.
- `backend/`: FastAPI backend application.
- `frontend/`: Vite React frontend application.

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
"# CE_AI_ASSISTANT"    # �إߤ@��²�檺 README.md
