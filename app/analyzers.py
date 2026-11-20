"""The fields Tarikh reads from each paper, and the Content Understanding analyzer built from them."""
from __future__ import annotations

from dataclasses import dataclass

from .models import DocType

DATE_NOTE = " Indian papers write the day first (DD-MM-YYYY)."


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    type: str                # string | date | number
    description: str
    manual: bool = False     # not on the paper; the lawyer supplies it
    manual_hint: str = ""


FIELD_SPECS: dict[DocType, list[FieldSpec]] = {
    DocType.CHEQUE: [
        FieldSpec("cheque_number", "Cheque number", "string", "The printed cheque number."),
        FieldSpec("cheque_date", "Date on cheque", "date", "The date written on the cheque." + DATE_NOTE),
        FieldSpec("amount_figures", "Amount (figures)", "number", "The amount in figures in rupees, digits only."),
        FieldSpec("drawer_name", "Drawer", "string", "The person or firm that signed the cheque (the account holder)."),
        FieldSpec("payee_name", "Payee", "string", "The name written after 'Pay'."),
        FieldSpec("bank_name", "Drawee bank", "string", "The bank the cheque is drawn on."),
    ],
    DocType.RETURN_MEMO: [
        FieldSpec("cheque_number", "Cheque number", "string", "The cheque number the memo refers to."),
        FieldSpec("presented_on", "Presented on", "date", "The date the cheque was presented." + DATE_NOTE),
        FieldSpec("return_date", "Returned on", "date", "The date the bank returned the cheque." + DATE_NOTE),
        FieldSpec("return_reason", "Reason for return", "string", "The reason the bank gives for returning the cheque unpaid."),
        FieldSpec("memo_received_on", "Memo received by payee", "date", "", True,
                  "Not on the paper. Enter the date the bank's memo reached the payee."),
    ],
    DocType.DEMAND_NOTICE: [
        FieldSpec("cheque_number", "Cheque number", "string", "The cheque number the notice refers to."),
        FieldSpec("notice_date", "Notice dated", "date", "The date written at the top of the notice." + DATE_NOTE),
        FieldSpec("demand_amount", "Amount demanded", "number", "The amount the notice demands, in rupees, digits only."),
        FieldSpec("notice_sent_on", "Notice posted on", "date", "", True,
                  "Not on the paper. Enter the date it was posted, from the postal receipt."),
        FieldSpec("notice_delivered_on", "Notice received by drawer", "date", "", True,
                  "Not on the paper. Enter the delivery date from the postal tracking record."),
    ],
}

_IDS = {DocType.CHEQUE: "tarikh-cheque", DocType.RETURN_MEMO: "tarikh-return-memo",
        DocType.DEMAND_NOTICE: "tarikh-demand-notice"}
_TITLES = {DocType.CHEQUE: "Cheque", DocType.RETURN_MEMO: "Bank return memo",
           DocType.DEMAND_NOTICE: "Demand notice"}


def analyzer_id(doc_type: DocType) -> str:
    return _IDS[doc_type]


def build_analyzer_definition(doc_type: DocType) -> dict:
    """REST-shaped analyzer definition (verified against the SDK's own serialisation)."""
    fields = {
        s.key: {"type": s.type, "method": "extract", "description": s.description,
                "estimateSourceAndConfidence": True}
        for s in FIELD_SPECS[doc_type] if not s.manual
    }
    return {
        "baseAnalyzerId": "prebuilt-document",
        "description": f"Tarikh: reads a {_TITLES[doc_type].lower()} for a cheque-dishonour matter.",
        "config": {"returnDetails": True, "estimateFieldSourceAndConfidence": True, "locales": ["en", "hi"]},
        "fieldSchema": {"name": _TITLES[doc_type], "fields": fields},
        "models": {"completion": "gpt-4.1"},
    }
