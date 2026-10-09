from typing import List

from pydantic import BaseModel, ConfigDict, Field


class Header(BaseModel):
    model_config = ConfigDict(extra="ignore")

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
    model_config = ConfigDict(extra="ignore")

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
    model_config = ConfigDict(extra="ignore")

    subtotal: float = 0
    total_discount: float = 0
    total_vat: float = 0
    rounding: float = 0
    grand_total: float = 0
    amount_paid: float = 0
    balance_due: float = 0


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    header: Header
    body: List[BodyItem] = Field(default_factory=list)
    summary: Summary