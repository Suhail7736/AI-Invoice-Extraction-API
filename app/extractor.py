from google import genai

from .prompts import EXTRACTION_PROMPT
from .schemas import InvoiceResponse


MODEL_NAME = "gemini-2.5-flash"


def extract_invoice(client, file_path, mime_type):
    """
    Extract structured invoice information using Gemini.

    Args:
        client: Initialized Gemini client.
        file_path: Path to the temporary invoice file.
        mime_type: MIME type of the uploaded file.

    Returns:
        InvoiceResponse: Validated invoice information.
    """

    uploaded_file = client.files.upload(
        file=file_path,
        config={
            "mime_type": mime_type
        }
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                uploaded_file,
                EXTRACTION_PROMPT
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": InvoiceResponse,
                "temperature": 0
            }
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        invoice = InvoiceResponse.model_validate_json(
            response.text
        )

        return invoice

    finally:
        # Attempt to remove the uploaded Gemini file.
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            # Cleanup failure should not hide the extraction result.
            pass