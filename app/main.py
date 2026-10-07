import json
import os
import tempfile

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from google import genai

from .extractor import extract_invoice
from .schemas import InvoiceResponse


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

load_dotenv(override=True)
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. "
        "Please add it to the .env file."
    )


# --------------------------------------------------
# Gemini Client
# --------------------------------------------------

client = genai.Client(
    api_key=API_KEY
)


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="AI Invoice Extraction API",
    description=(
        "AI-powered API for extracting structured "
        "data from PDF and image invoices."
    ),
    version="1.0.0"
)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI Invoice Extraction API",
        "status": "running"
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "gemini": "connected"
    }


# --------------------------------------------------
# Invoice Extraction
# --------------------------------------------------

@app.post(
    "/extract-invoice",
    response_model=InvoiceResponse
)
async def extract_invoice_api(
    file: UploadFile = File(...)
):

    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    filename = file.filename or ""

    extension = os.path.splitext(
        filename.lower()
    )[1]

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF, JPG, JPEG, PNG and WEBP "
                "files are supported."
            )
        )

    mime_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }

    mime_type = mime_types[extension]

    file_data = await file.read()

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    temporary_file = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp:

            temp.write(file_data)
            temporary_file = temp.name

        invoice = extract_invoice(
            client,
            temporary_file,
            mime_type
        )

        return JSONResponse(
            content=json.loads(
                invoice.model_dump_json()
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Invoice extraction failed: {str(e)}"
        )

    finally:

        if (
            temporary_file
            and os.path.exists(temporary_file)
        ):
            os.remove(temporary_file)