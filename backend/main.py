from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
import google.generativeai as genai
import tempfile
import os

# =========================
# GEMINI CONFIG
# =========================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# FASTAPI
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MEMORY
# =========================

documents = []
chat_history = []

# =========================
# MODELS
# =========================

class Question(BaseModel):
    question: str
    selected_doc: str

# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {
        "message": "DocuMind AI Backend Running"
    }

# =========================
# UPLOAD PDF
# =========================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp:

            temp.write(await file.read())
            temp_path = temp.name

        reader = PdfReader(temp_path)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        documents.append(
            {
                "filename": file.filename,
                "content": text
            }
        )

        return {
            "success": True,
            "filename": file.filename,
            "documents": len(documents)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================
# DOCUMENTS
# =========================

@app.get("/documents")
def get_documents():

    return {
        "documents": [
            doc["filename"]
            for doc in documents
        ]
    }

# =========================
# ASK QUESTION
# =========================

@app.post("/ask")
async def ask(data: Question):

    try:

        if len(documents) == 0:

            return {
                "answer": "Please upload at least one PDF."
            }

        selected_content = ""

        for doc in documents:

            if doc["filename"] == data.selected_doc:
                selected_content = doc["content"]
                break

        if not selected_content:

            return {
                "answer": "Please select a document."
            }

        recent_history = chat_history[-10:]

        prompt = f"""
You are DocuMind AI.

You are an enterprise knowledge assistant.

Answer ONLY from the uploaded document.

DOCUMENT:
{selected_content[:12000]}

CHAT HISTORY:
{recent_history}

QUESTION:
{data.question}

Rules:
1. Answer only from the document.
2. Be concise and professional.
3. If information is unavailable, say:
   Information not found in uploaded document.
"""

        response = model.generate_content(prompt)

        answer = response.text

        chat_history.append(
            {
                "role": "user",
                "content": data.question
            }
        )

        chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return {
            "answer": answer
        }

    except Exception as e:

        return {
            "answer": f"Gemini Error: {str(e)}"
        }

# =========================
# HISTORY
# =========================

@app.get("/history")
def history():

    return {
        "history": chat_history
    }

# =========================
# CLEAR CHAT
# =========================

@app.post("/clear")
def clear_chat():

    chat_history.clear()

    return {
        "message": "Chat history cleared"
    }