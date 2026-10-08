# AI Invoice Extraction API

An AI-powered REST API for extracting structured information from invoice PDFs and images using **FastAPI** and **Google Gemini 2.5 Flash**.

## Overview

This project provides an API that accepts invoices in PDF and image formats and extracts important invoice information into a predefined JSON structure.

The system uses Google Gemini's vision capabilities to understand invoice content based on:

- Text
- Labels
- Visual layout
- Tables
- Semantic meaning

The extraction process does not depend on fixed coordinates or a single invoice template. Different invoice layouts, field positions, and terminology can be mapped into the same standardized response schema.

---

## Key Features

- PDF invoice extraction
- JPG, JPEG, PNG and WEBP image support
- AI-based invoice understanding
- Layout-independent extraction
- Semantic field mapping
- Header information extraction
- Customer information extraction
- Line-item extraction
- Tax / VAT information extraction
- Invoice summary extraction
- Structured JSON response
- Pydantic schema validation
- FastAPI REST API
- Swagger / OpenAPI documentation
- Temporary file handling
- Environment-based API key configuration

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Application development |
| FastAPI | REST API framework |
| Google Gemini 2.5 Flash | AI-based invoice extraction |
| Google GenAI SDK | Gemini API integration |
| Pydantic | Data validation and structured response |
| Uvicorn | ASGI server |
| python-dotenv | Environment variable management |

---

## 📁 Project Structure

AI-Invoice-Extraction-API/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── extractor.py
│   ├── prompts.py
│   └── schemas.py
│
├── samples/
│   ├── sample_invoice.pdf
│   └── second_invoice.png
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
---

## System Architecture

```text
                 Invoice PDF / Image
                         |
                         v
                FastAPI Upload API
                         |
                         v
                  File Validation
                         |
                         v
                 Temporary Storage
                         |
                         v
              Google Gemini 2.5 Flash
                         |
                         v
             Semantic Field Extraction
                         |
                         v
                Pydantic Validation
                         |
                         v
                Structured JSON
                         |
                         v
                    API Response
