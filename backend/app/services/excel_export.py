"""Export event data to Excel."""
from io import BytesIO
from typing import List, TypedDict, Optional
from datetime import datetime
import openpyxl

from app.models import Event, Resident


class LogEntryForExport(TypedDict):
    created_at: Optional[datetime]
    author_type: str
    message: str
    author_name: str


def _resident_display_name(r: Resident) -> str:
    return f"{(r.first_name or '')} {(r.last_name or '')}".strip() or "—"


def export_event_to_excel(
    event: Event,
    residents: List[Resident],
    log_entries: List[LogEntryForExport],
) -> BytesIO:
    buffer = BytesIO()
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "תושבים"
    ws1.append(["סוג", "שם", "כתובת", "טלפון", "סטטוס", "הערות"])
    for r in residents:
        kind = "מזדמן" if r.source == "casual" else "תושב"
        ws1.append([
            kind,
            _resident_display_name(r),
            r.address,
            r.phone or "",
            r.status.value,
            r.volunteer_notes or r.notes or "",
        ])
    ws2 = wb.create_sheet("יומן אירוע")
    ws2.append(["תאריך", "סוג", "כותב", "הודעה"])
    for e in log_entries:
        created = e["created_at"]
        ws2.append([
            created.isoformat() if created else "",
            e["author_type"],
            e["author_name"],
            e["message"],
        ])
    wb.save(buffer)
    buffer.seek(0)
    return buffer
