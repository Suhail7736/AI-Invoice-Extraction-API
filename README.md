# AI Invoice Extraction API

An AI-powered REST API that extracts structured information from invoice PDFs and images using Google Gemini Vision and FastAPI.

## Overview

The API accepts invoice files in PDF and image formats and uses Google Gemini to understand the invoice content, identify fields based on their semantic meaning, and map them into a predefined JSON schema.

The implementation does not depend on fixed invoice coordinates or a specific invoice template.

## Features

- PDF invoice extraction
- JPG, JPEG, PNG and WEBP support
- AI-based invoice understanding
- Layout-independent field extraction
- Semantic field mapping
- Header information extraction
- Line-item extraction
- Customer information extraction
- Tax/VAT information extraction
- Invoice summary extraction
- Pydantic schema validation
- FastAPI REST API
- Swagger/OpenAPI documentation
- Temporary file handling
- Structured JSON response

## Technology Stack

- Python 3.11
- FastAPI
- Google Gemini 2.5 Flash
- Google GenAI SDK
- Pydantic
- Uvicorn
- python-dotenv

## Project Structure

```text
AI-Invoice-Extraction-API/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── extractor.py
│   ├── prompts.py
│   ├── schemas.py
│   └── table_parser.py
│
├── .gitignore
├── requirements.txt
└── README.md
