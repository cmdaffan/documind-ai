from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
import tempfile
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

documents = []
chat_history = []


class Question(BaseModel):
    question: str
    selected_doc: str


@app.get("/")
def home():
    return {"message": "DocuMind AI Backend Running"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
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


@app.get("/documents")
def get_documents():

    return {
        "documents": [
            doc["filename"]
            for doc in documents
        ]
    }


@app.post("/ask")
async def ask(data: Question):

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

    chat_history.append(
        {
            "role": "user",
            "content": data.question
        }
    )

    recent_history = chat_history[-10:]

    prompt = f"""
You are DocuMind AI.

You are an enterprise knowledge assistant.

Answer ONLY using the document content below.

DOCUMENT:
{selected_content[:12000]}

CHAT HISTORY:
{recent_history}

QUESTION:
{data.question}

Rules:
- Be professional.
- If answer is not found, say so.
- Keep answers concise and useful.
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        answer = response.json()["response"]

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
            "answer": f"AI Error: {str(e)}"
        }


@app.get("/history")
def history():

    return {
        "history": chat_history
    }


@app.post("/clear")
def clear_chat():

    chat_history.clear()

    return {
        "message": "Chat history cleared"
    }