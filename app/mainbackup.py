from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pymupdf
import pytesseract
from PIL import Image
import io
import requests
import json
import re
from pydantic import BaseModel
from typing import List


app = FastAPI(
    title="AI Invoice Extraction API",
    version="1.0.0"
)


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"


class Header(BaseModel):
    invoice_no: str = ""
    invoice_date: str = ""
    due_date: str = ""
    customer: str = ""
    customer_code: str = ""
    address: str = ""
    phno: str = ""
    email: str = ""
    tax_registration_no: str = ""
    currency: str = ""
    payment_terms: str = ""
    narration: str = ""


class BodyItem(BaseModel):
    product_name: str = ""
    product_code: str = ""
    description: str = ""
    unit: str = ""
    qty: float = 0
    rate: float = 0
    gross: float = 0
    discount: float = 0
    vat_rate: float = 0
    vat: float = 0
    net: float = 0


class Summary(BaseModel):
    subtotal: float = 0
    total_discount: float = 0
    total_vat: float = 0
    rounding: float = 0
    grand_total: float = 0
    amount_paid: float = 0
    balance_due: float = 0


class InvoiceResponse(BaseModel):
    header: Header
    body: List[BodyItem]
    summary: Summary


def clean_number(value):

    if value is None:
        return 0

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    value = value.replace(",", "")
    value = value.replace("₹", "")
    value = value.replace("$", "")
    value = value.replace("€", "")
    value = value.replace("£", "")
    value = value.replace("AED", "")
    value = value.replace("INR", "")

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        value
    )

    if not match:
        return 0

    try:
        return float(match.group())
    except ValueError:
        return 0


def normalize_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text)
    ).strip()


def extract_pdf_text(file_bytes):

    doc = pymupdf.open(
        stream=file_bytes,
        filetype="pdf"
    )

    text = ""

    for page in doc:
        text += page.get_text()
        text += "\n"

    doc.close()

    return text


def extract_ocr(file_bytes, file_type):

    if file_type == "pdf":

        doc = pymupdf.open(
            stream=file_bytes,
            filetype="pdf"
        )

        text = ""

        for page in doc:

            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2)
            )

            image_bytes = pix.tobytes(
                "png"
            )

            image = Image.open(
                io.BytesIO(image_bytes)
            )

            text += pytesseract.image_to_string(
                image
            )

            text += "\n"

        doc.close()

        return text

    image = Image.open(
        io.BytesIO(file_bytes)
    )

    return pytesseract.image_to_string(
        image
    )


def ask_ai(text):

    prompt = f"""
You are an AI invoice extraction system.

Extract information from the invoice text.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "header": {{
    "invoice_no": "",
    "invoice_date": "",
    "due_date": "",
    "customer": "",
    "customer_code": "",
    "address": "",
    "phno": "",
    "email": "",
    "tax_registration_no": "",
    "currency": "",
    "payment_terms": "",
    "narration": ""
  }},
  "body": [
    {{
      "product_name": "",
      "product_code": "",
      "description": "",
      "unit": "",
      "qty": 0,
      "rate": 0,
      "gross": 0,
      "discount": 0,
      "vat_rate": 0,
      "vat": 0,
      "net": 0
    }}
  ],
  "summary": {{
    "subtotal": 0,
    "total_discount": 0,
    "total_vat": 0,
    "rounding": 0,
    "grand_total": 0,
    "amount_paid": 0,
    "balance_due": 0
  }}
}}

Rules:

1. Return only JSON.
2. Do not add markdown.
3. Do not invent information.
4. If a text field is missing, use "".
5. If a numeric field is missing, use 0.
6. Preserve all invoice line items.
7. Identify fields by their meaning.
8. Different invoices may use different labels.
9. Invoice Number, Invoice No, Bill No and similar labels map to invoice_no.
10. Bill To, Buyer, Customer and similar labels map to customer.
11. VAT, GST and Tax should be mapped according to the invoice.
12. Amount Paid, Paid Amount and Payment Received map to amount_paid.
13. Balance, Balance Due and Amount Due map to balance_due.

Invoice text:

{text}
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },
            timeout=180
        )

    except requests.RequestException as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not connect to Ollama: {str(e)}"
        )

    if response.status_code != 200:

        raise HTTPException(
            status_code=500,
            detail="Ollama request failed"
        )

    result = response.json()

    raw = result.get(
        "response",
        ""
    ).strip()

    raw = re.sub(
        r"```json",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"```",
        "",
        raw
    ).strip()

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1:

        raise HTTPException(
            status_code=500,
            detail="AI did not return valid JSON"
        )

    raw = raw[start:end + 1]

    try:

        return json.loads(raw)

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="Invalid JSON returned by AI"
        )


def find_header_columns(page):

    words = page.get_text(
        "words"
    )

    if not words:
        return {}

    rows = {}

    for word in words:

        x0, y0, x1, y1, text = word[:5]

        row_key = round(y0 / 4) * 4

        if row_key not in rows:
            rows[row_key] = []

        rows[row_key].append(
            {
                "text": text.strip(),
                "x": (x0 + x1) / 2,
                "y": (y0 + y1) / 2
            }
        )

    aliases = {

        "product_name": [
            "product",
            "item",
            "description",
            "productname",
            "itemname",
            "particulars"
        ],

        "product_code": [
            "code",
            "sku",
            "itemcode",
            "productcode",
            "itemno",
            "itemnumber"
        ],

        "unit": [
            "unit",
            "uom"
        ],

        "qty": [
            "qty",
            "quantity"
        ],

        "rate": [
            "rate",
            "price",
            "unitprice",
            "unitcost"
        ],

        "gross": [
            "gross",
            "grossamount"
        ],

        "discount": [
            "discount",
            "disc",
            "discountamount"
        ],

        "vat_rate": [
            "vatrate",
            "taxrate",
            "gst",
            "gstrate",
            "vat%"
        ],

        "vat": [
            "vatamount",
            "taxamount",
            "gstamount",
            "tax"
        ],

        "net": [
            "net",
            "total",
            "netamount",
            "lineamount"
        ]
    }

    best_row = None
    best_score = 0

    for row in rows.values():

        score = 0

        for word in row:

            cleaned = re.sub(
                r"[^a-zA-Z%]",
                "",
                word["text"].lower()
            )

            for field_names in aliases.values():

                if cleaned in field_names:

                    score += 1
                    break

        if score > best_score:

            best_score = score
            best_row = row

    if not best_row or best_score < 3:
        return {}

    columns = {}

    for word in best_row:

        cleaned = re.sub(
            r"[^a-zA-Z%]",
            "",
            word["text"].lower()
        )

        matched_field = None

        for field, names in aliases.items():

            if cleaned in names:

                matched_field = field
                break

        if matched_field is None:
            continue

        if matched_field not in columns:

            columns[matched_field] = word["x"]

    return columns


def find_table_rows(page, header_columns):

    if not header_columns:
        return []

    words = page.get_text(
        "words"
    )

    if not words:
        return []

    rows = {}

    for word in words:

        x0, y0, x1, y1, text = word[:5]

        row_key = round(y0 / 4) * 4

        if row_key not in rows:
            rows[row_key] = []

        rows[row_key].append(
            {
                "text": text.strip(),
                "x": (x0 + x1) / 2,
                "y": (y0 + y1) / 2
            }
        )

    header_y = None

    for y, row in rows.items():

        row_text = " ".join(
            item["text"].lower()
            for item in row
        )

        has_quantity = (
            "qty" in row_text
            or "quantity" in row_text
        )

        has_rate = (
            "rate" in row_text
            or "price" in row_text
        )

        if has_quantity and has_rate:

            header_y = y
            break

    if header_y is None:
        return []

    sorted_columns = sorted(
        header_columns.items(),
        key=lambda x: x[1]
    )

    result = []

    stop_words = [
        "subtotal",
        "grand total",
        "amount paid",
        "balance due",
        "total discount",
        "total vat",
        "rounding",
        "amount due"
    ]

    for y, row in sorted(rows.items()):

        if y <= header_y:
            continue

        row_text = " ".join(
            item["text"].lower()
            for item in row
        )

        if any(
            stop_word in row_text
            for stop_word in stop_words
        ):
            continue

        if len(row) < 3:
            continue

        mapped = {}

        for word in row:

            nearest_field = None
            nearest_distance = float("inf")

            for field, x_position in sorted_columns:

                distance = abs(
                    word["x"] - x_position
                )

                if distance < nearest_distance:

                    nearest_distance = distance
                    nearest_field = field

            if nearest_field is None:
                continue

            if nearest_field not in mapped:

                mapped[nearest_field] = word["text"]

            else:

                mapped[nearest_field] += (
                    " " + word["text"]
                )

        if len(mapped) >= 3:

            result.append(mapped)

    return result


def parse_pdf_table(file_bytes):

    doc = pymupdf.open(
        stream=file_bytes,
        filetype="pdf"
    )

    all_rows = []

    for page in doc:

        columns = find_header_columns(
            page
        )

        if not columns:
            continue

        rows = find_table_rows(
            page,
            columns
        )

        all_rows.extend(rows)

    doc.close()

    body = []

    for row in all_rows:

        product_name = normalize_text(
            row.get(
                "product_name",
                ""
            )
        )

        product_code = normalize_text(
            row.get(
                "product_code",
                ""
            )
        )

        unit = normalize_text(
            row.get(
                "unit",
                ""
            )
        )

        item = BodyItem(

            product_name=product_name,

            product_code=product_code,

            description=product_name,

            unit=unit,

            qty=clean_number(
                row.get("qty", 0)
            ),

            rate=clean_number(
                row.get("rate", 0)
            ),

            gross=clean_number(
                row.get("gross", 0)
            ),

            discount=clean_number(
                row.get("discount", 0)
            ),

            vat_rate=clean_number(
                row.get("vat_rate", 0)
            ),

            vat=clean_number(
                row.get("vat", 0)
            ),

            net=clean_number(
                row.get("net", 0)
            )
        )

        if (
            item.product_name
            and (
                item.qty > 0
                or item.rate > 0
                or item.gross > 0
                or item.net > 0
            )
        ):

            body.append(item)

    return body


def validate_item(item):

    calculated_gross = (
        item.qty * item.rate
    )

    if (
        item.gross == 0
        and calculated_gross > 0
    ):

        item.gross = calculated_gross

    taxable_amount = (
        item.gross - item.discount
    )

    if (
        item.vat == 0
        and item.net > 0
        and taxable_amount >= 0
    ):

        calculated_vat = (
            item.net - taxable_amount
        )

        if calculated_vat > 0:

            item.vat = calculated_vat

    if (
        item.discount == 0
        and item.net > 0
    ):

        calculated_discount = (
            item.gross
            + item.vat
            - item.net
        )

        if calculated_discount > 0:

            item.discount = (
                calculated_discount
            )

    taxable_amount = (
        item.gross - item.discount
    )

    if (
        item.vat_rate == 0
        and item.vat > 0
        and taxable_amount > 0
    ):

        item.vat_rate = (
            item.vat
            / taxable_amount
            * 100
        )

    if (
        item.net == 0
        and (
            item.gross > 0
            or item.vat > 0
        )
    ):

        item.net = (
            item.gross
            - item.discount
            + item.vat
        )

    item.qty = round(
        item.qty,
        2
    )

    item.rate = round(
        item.rate,
        2
    )

    item.gross = round(
        item.gross,
        2
    )

    item.discount = round(
        item.discount,
        2
    )

    item.vat_rate = round(
        item.vat_rate,
        2
    )

    item.vat = round(
        item.vat,
        2
    )

    item.net = round(
        item.net,
        2
    )

    return item


def create_header(data):

    if not isinstance(
        data,
        dict
    ):
        data = {}

    return Header(

        invoice_no=str(
            data.get(
                "invoice_no",
                ""
            ) or ""
        ),

        invoice_date=str(
            data.get(
                "invoice_date",
                ""
            ) or ""
        ),

        due_date=str(
            data.get(
                "due_date",
                ""
            ) or ""
        ),

        customer=str(
            data.get(
                "customer",
                ""
            ) or ""
        ),

        customer_code=str(
            data.get(
                "customer_code",
                ""
            ) or ""
        ),

        address=str(
            data.get(
                "address",
                ""
            ) or ""
        ),

        phno=str(
            data.get(
                "phno",
                ""
            ) or ""
        ),

        email=str(
            data.get(
                "email",
                ""
            ) or ""
        ),

        tax_registration_no=str(
            data.get(
                "tax_registration_no",
                ""
            ) or ""
        ),

        currency=str(
            data.get(
                "currency",
                ""
            ) or ""
        ),

        payment_terms=str(
            data.get(
                "payment_terms",
                ""
            ) or ""
        ),

        narration=str(
            data.get(
                "narration",
                ""
            ) or ""
        )
    )


def create_summary(data):

    if not isinstance(
        data,
        dict
    ):
        data = {}

    return Summary(

        subtotal=clean_number(
            data.get(
                "subtotal",
                0
            )
        ),

        total_discount=clean_number(
            data.get(
                "total_discount",
                0
            )
        ),

        total_vat=clean_number(
            data.get(
                "total_vat",
                0
            )
        ),

        rounding=clean_number(
            data.get(
                "rounding",
                0
            )
        ),

        grand_total=clean_number(
            data.get(
                "grand_total",
                0
            )
        ),

        amount_paid=clean_number(
            data.get(
                "amount_paid",
                0
            )
        ),

        balance_due=clean_number(
            data.get(
                "balance_due",
                0
            )
        )
    )


def create_ai_body(data):

    if not isinstance(
        data,
        list
    ):
        return []

    body = []

    for row in data:

        if not isinstance(
            row,
            dict
        ):
            continue

        item = BodyItem(

            product_name=str(
                row.get(
                    "product_name",
                    ""
                ) or ""
            ),

            product_code=str(
                row.get(
                    "product_code",
                    ""
                ) or ""
            ),

            description=str(
                row.get(
                    "description",
                    ""
                ) or ""
            ),

            unit=str(
                row.get(
                    "unit",
                    ""
                ) or ""
            ),

            qty=clean_number(
                row.get(
                    "qty",
                    0
                )
            ),

            rate=clean_number(
                row.get(
                    "rate",
                    0
                )
            ),

            gross=clean_number(
                row.get(
                    "gross",
                    0
                )
            ),

            discount=clean_number(
                row.get(
                    "discount",
                    0
                )
            ),

            vat_rate=clean_number(
                row.get(
                    "vat_rate",
                    0
                )
            ),

            vat=clean_number(
                row.get(
                    "vat",
                    0
                )
            ),

            net=clean_number(
                row.get(
                    "net",
                    0
                )
            )
        )

        body.append(
            validate_item(item)
        )

    return body


def merge_results(
    ai_data,
    pdf_body
):

    if not isinstance(
        ai_data,
        dict
    ):
        ai_data = {}

    header = create_header(
        ai_data.get(
            "header",
            {}
        )
    )

    summary = create_summary(
        ai_data.get(
            "summary",
            {}
        )
    )

    ai_body = create_ai_body(
        ai_data.get(
            "body",
            []
        )
    )

    final_body = []

    if pdf_body:

        for index, pdf_item in enumerate(
            pdf_body
        ):

            pdf_item = validate_item(
                pdf_item
            )

            if index < len(ai_body):

                ai_item = ai_body[index]

                if not pdf_item.product_name:

                    pdf_item.product_name = (
                        ai_item.product_name
                    )

                if not pdf_item.product_code:

                    pdf_item.product_code = (
                        ai_item.product_code
                    )

                if not pdf_item.description:

                    pdf_item.description = (
                        ai_item.description
                    )

                if not pdf_item.unit:

                    pdf_item.unit = (
                        ai_item.unit
                    )

            final_body.append(
                pdf_item
            )

    else:

        final_body = ai_body

    return InvoiceResponse(
        header=header,
        body=final_body,
        summary=summary
    )


@app.get("/")
def home():

    return {
        "message": "AI Invoice Extraction API is running",
        "status": "success"
    }


@app.get("/health")
def health():

    try:

        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )

        ollama_status = (
            response.status_code == 200
        )

    except:

        ollama_status = False

    return {
        "api": "running",
        "ollama": ollama_status,
        "model": MODEL
    }


@app.post(
    "/extract-invoice",
    response_model=InvoiceResponse
)
async def extract_invoice(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    filename = file.filename.lower()

    allowed_extensions = (
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    )

    if not filename.endswith(
        allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF and image files are supported"
        )

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if filename.endswith(".pdf"):

        file_type = "pdf"

        text = extract_pdf_text(
            file_bytes
        )

        if not text.strip():

            text = extract_ocr(
                file_bytes,
                "pdf"
            )

    else:

        file_type = "image"

        text = extract_ocr(
            file_bytes,
            "image"
        )

    if not text.strip():

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from invoice"
        )

    ai_data = ask_ai(
        text
    )

    pdf_body = []

    if file_type == "pdf":

        pdf_body = parse_pdf_table(
            file_bytes
        )

    result = merge_results(
        ai_data,
        pdf_body
    )

    return JSONResponse(
        content=result.model_dump()
    )