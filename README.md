# QwenArch — Codebase to Miro Architecture Engine

QwenArch connects **Qwen's code reasoning LLM** with **Miro's interactive whiteboard canvas** to ingest codebases and generate live, editable system architecture diagrams.

## 🚀 One-Click Vercel Deployment

1. Drag-and-drop the `qwenarch-vercel.zip` file or connect your GitHub repository to Vercel.
2. Under **Project Settings > Environment Variables**, configure:
   - `MIRO_ACCESS_TOKEN` : Your Miro OAuth token (`eyJ...`)
   - `MIRO_BOARD_ID` : Your target Miro Board ID (e.g. `uXjVEekRCSA=`)
   - `MODELSCOPE_API_KEY` : `your_modelscope_api_key_here`
   - `MODELSCOPE_BASE_URL` : `https://api-inference.modelscope.ai/v1`
   - `MODELSCOPE_MODEL` : `Qwen/Qwen3.8-27B`
3. Click **Deploy**.

## 💻 Local Development

```bash
# 1. Start FastAPI Backend
cd backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 2. Start Frontend
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to use the application.
