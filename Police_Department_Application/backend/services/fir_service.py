"""FIR PDF generation service"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from config import settings


def _ensure_directory() -> str:
    """Ensure the FIR directory exists and return its path."""
    directory = settings.fir_reports_directory
    os.makedirs(directory, exist_ok=True)
    return directory


def _format_kv(canvas_obj: canvas.Canvas, x: float, y: float, label: str, value: str, font_size: int = 11):
    canvas_obj.setFont("Helvetica-Bold", font_size)
    canvas_obj.drawString(x, y, f"{label}: ")
    canvas_obj.setFont("Helvetica", font_size)
    canvas_obj.drawString(x + 65 * mm, y, value)


def generate_fir_pdf(incident: Dict[str, Any]) -> str:
    """Generate an FIR PDF for the provided incident dictionary and return filename."""
    directory = _ensure_directory()
    filename = f"fir_{incident['alert_id']}_{int(datetime.utcnow().timestamp())}.pdf"
    file_path = os.path.join(directory, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    margin = 20 * mm
    current_y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, current_y, "Police SEDI - Electronic FIR")
    current_y -= 12 * mm

    c.setFont("Helvetica", 10)
    c.drawString(margin, current_y, f"Generated At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)")
    current_y -= 10 * mm

    # Incident information
    _format_kv(c, margin, current_y, "Alert ID", str(incident.get("alert_id", "-")))
    current_y -= 8 * mm
    _format_kv(c, margin, current_y, "Tourist ID", str(incident.get("tourist_id", "-")))
    current_y -= 8 * mm
    _format_kv(c, margin, current_y, "Incident Type", str(incident.get("type", "-")))
    current_y -= 8 * mm
    _format_kv(c, margin, current_y, "Status", str(incident.get("last_status", "-")))
    current_y -= 8 * mm
    created_at = incident.get("created_at") or "-"
    _format_kv(c, margin, current_y, "Reported On", str(created_at))
    current_y -= 8 * mm

    # Location
    loc = incident.get("location") or {}
    location_text = "Unavailable"
    if loc.get("lat") is not None and loc.get("lng") is not None:
        location_text = f"Lat: {loc['lat']}, Lng: {loc['lng']}, Accuracy: {loc.get('accuracy', 'N/A')}"
    _format_kv(c, margin, current_y, "Location", location_text)
    current_y -= 8 * mm

    score = incident.get("score_band") or "-"
    _format_kv(c, margin, current_y, "Risk Score", score)
    current_y -= 12 * mm

    # Details box
    details = incident.get("details") or "No additional details provided."
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y, "Incident Details")
    current_y -= 8 * mm

    text_obj = c.beginText()
    text_obj.setTextOrigin(margin, current_y)
    text_obj.setFont("Helvetica", 11)
    for line in details.split('\n'):
        text_obj.textLine(line)
    c.drawText(text_obj)
    current_y = text_obj.getY() - 12 * mm

    # Footer
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(margin, margin, "This FIR was generated automatically by the Police SEDI system.")
    c.drawRightString(width - margin, margin, "Internal Use Only")

    c.save()
    return filename


def get_fir_file(filename: str) -> Optional[str]:
    """Return absolute path for FIR file if it exists."""
    directory = _ensure_directory()
    file_path = os.path.join(directory, filename)
    if os.path.exists(file_path):
        return file_path
    return None


