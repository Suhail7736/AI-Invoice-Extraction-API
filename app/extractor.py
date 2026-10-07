from google import genai

from .schemas import InvoiceResponse
from .prompts import EXTRACTION_PROMPT


MODEL_NAME = "gemini-2.5-flash"


def extract_invoice(client, file_path, mime_type):
    """
    Upload the invoice to Gemini and extract structured invoice data.
    """

    uploaded_file = client.files.upload(
        file=file_path,
        config={
            "mime_type": mime_type
        }
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            uploaded_file,
            EXTRACTION_PROMPT
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": InvoiceResponse
        }
    )

    invoice = InvoiceResponse.model_validate_json(
        response.text
    )

    return invoice