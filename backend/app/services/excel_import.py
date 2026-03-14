from typing import List, Tuple
from io import BytesIO, StringIO
import csv
import openpyxl
from pydantic import ValidationError

from app.schemas.resident import ResidentRow

# Expected column names (Hebrew or English)
COLUMN_ALIASES = {
    "first_name": ["שם פרטי", "first_name", "first name", "שם"],
    "last_name": ["שם משפחה", "last_name", "last name", "משפחה"],
    "address": ["כתובת", "address", "רחוב", "דירה"],
    "phone": ["טלפון", "phone", "phone number"],
    "notes": ["הערות", "notes", "הערות מקדימות"],
}


def _normalize_header(h: str) -> str:
    return (h or "").strip().lower()


def _find_column_index(headers: List[str]) -> dict:
    """Map field name to 0-based column index from first row."""
    result = {}
    for idx, cell in enumerate(headers):
        val = _normalize_header(str(cell) if cell is not None else "")
        for field, aliases in COLUMN_ALIASES.items():
            if val in [a.strip().lower() for a in aliases]:
                result[field] = idx
                break
    return result


def parse_residents_excel(content: bytes) -> Tuple[List[ResidentRow], List[str]]:
    """Parse Excel file, return list of valid ResidentRow and list of error messages."""
    wb = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    if not ws:
        return [], ["גיליון ריק"]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], ["אין שורות"]
    headers = list(rows[0])
    col = _find_column_index(headers)
    if "first_name" not in col or "last_name" not in col or "address" not in col:
        return [], ["חסרות עמודות נדרשות: שם פרטי, שם משפחה, כתובת"]
    out: List[ResidentRow] = []
    errors: List[str] = []
    for i, row in enumerate(rows[1:], start=2):
        if not any(cell is not None for cell in row):
            continue
        first_name = row[col["first_name"]] if col["first_name"] < len(row) else None
        last_name = row[col["last_name"]] if col["last_name"] < len(row) else None
        address = row[col["address"]] if col["address"] < len(row) else None
        phone = row[col["phone"]] if "phone" in col and col["phone"] < len(row) else None
        notes = row[col["notes"]] if "notes" in col and col["notes"] < len(row) else None
        first_name = str(first_name).strip() if first_name is not None else ""
        last_name = str(last_name).strip() if last_name is not None else ""
        address = str(address).strip() if address is not None else ""
        phone = str(phone).strip() if phone else None
        notes = str(notes).strip() if notes else None
        try:
            out.append(
                ResidentRow(
                    first_name=first_name,
                    last_name=last_name,
                    address=address,
                    phone=phone or None,
                    notes=notes or None,
                )
            )
        except ValidationError as e:
            errors.append(f"שורה {i}: {e}")
    wb.close()
    return out, errors


def parse_residents_csv(content: bytes) -> Tuple[List[ResidentRow], List[str]]:
    """Parse CSV file (UTF-8), return list of valid ResidentRow and list of error messages."""
    try:
        text = content.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        return [], ["קובץ לא ב-UTF-8"]
    if not text:
        return [], ["קובץ ריק"]
    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if not rows:
        return [], ["אין שורות"]
    headers = rows[0]
    col = _find_column_index(headers)
    if "first_name" not in col or "last_name" not in col or "address" not in col:
        return [], ["חסרות עמודות נדרשות: שם פרטי, שם משפחה, כתובת"]
    out: List[ResidentRow] = []
    errors: List[str] = []
    for i, row in enumerate(rows[1:], start=2):
        if not row or not any(cell and str(cell).strip() for cell in row):
            continue
        first_name = row[col["first_name"]] if col["first_name"] < len(row) else ""
        last_name = row[col["last_name"]] if col["last_name"] < len(row) else ""
        address = row[col["address"]] if col["address"] < len(row) else ""
        phone = row[col["phone"]] if "phone" in col and col["phone"] < len(row) else ""
        notes = row[col["notes"]] if "notes" in col and col["notes"] < len(row) else ""
        first_name = str(first_name).strip() if first_name else ""
        last_name = str(last_name).strip() if last_name else ""
        address = str(address).strip() if address else ""
        phone = str(phone).strip() if phone else None
        notes = str(notes).strip() if notes else None
        try:
            out.append(
                ResidentRow(
                    first_name=first_name,
                    last_name=last_name,
                    address=address,
                    phone=phone or None,
                    notes=notes or None,
                )
            )
        except ValidationError as e:
            errors.append(f"שורה {i}: {e}")
    return out, errors


def parse_residents_file(content: bytes, filename: str) -> Tuple[List[ResidentRow], List[str]]:
    """Dispatch to Excel or CSV parser based on file extension."""
    fn = (filename or "").lower()
    if fn.endswith(".csv"):
        return parse_residents_csv(content)
    if fn.endswith(".xlsx") or fn.endswith(".xls"):
        return parse_residents_excel(content)
    return [], ["סוג קובץ לא נתמך. השתמש ב־CSV או Excel (xlsx)."]
