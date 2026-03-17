"""Export residents and event log to Excel."""
from datetime import datetime
from io import BytesIO
from typing import List, Optional, TypedDict

import openpyxl

from app.models import Event, Resident


class LogEntryForExport(TypedDict):
    created_at: Optional[datetime]
    author_type: str
    author_name: str
    message: str


def export_event_to_excel(
    event: Event,
    residents: List[Resident],
    log_entries: List[LogEntryForExport],
) -> BytesIO:
    buffer = BytesIO()
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "גיליון1"
    ws1.append(
        [
            "מספר זהות",
            "שם משפחה",
            "שם פרטי",
            "מין",
            "ישוב",
            "רחוב",
            "מס' בית",
            "דירה",
            "גיל",
            "טלפון נייד",
            "טלפון בבית",
            "הערות מקדימות",
            "סטטוס נוכחי",
            "הערות מתנדב",
            "מקור",
            "עודכן לאחרונה",
        ]
    )
    for r in residents:
        ws1.append(
            [
                r.identity_number or "",
                r.last_name or "",
                r.first_name or "",
                r.gender or "",
                r.city or "",
                r.street or "",
                r.house_number or "",
                r.apartment or "",
                r.age if r.age is not None else "",
                r.phone or "",
                r.home_phone or "",
                r.notes or "",
                r.status.value,
                r.volunteer_notes or "",
                r.source or "",
                r.updated_at.isoformat() if r.updated_at else "",
            ]
        )

    ws2 = wb.create_sheet("יומן אירוע")
    ws2.append(["תאריך", "סוג כותב", "שם כותב", "הודעה"])
    for entry in log_entries:
        created_at = entry["created_at"]
        ws2.append(
            [
                created_at.isoformat() if created_at else "",
                entry["author_type"],
                entry["author_name"],
                entry["message"],
            ]
        )

    wb.save(buffer)
    buffer.seek(0)
    return buffer
