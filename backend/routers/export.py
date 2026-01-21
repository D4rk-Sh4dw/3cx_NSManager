from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, NotfallPlan, AuditLog
from routers.auth import get_current_user
import csv
import io
from datetime import datetime

router = APIRouter(prefix="/export", tags=["export"])

def require_export_access(current_user: User = Depends(get_current_user)):
    """Allow admin and buchhaltung roles to export"""
    if current_user.role not in ["admin", "buchhaltung"]:
        raise HTTPException(
            status_code=403,
            detail="Export access requires admin or buchhaltung role"
        )
    return current_user

@router.get("/plans")
async def export_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_export_access)
):
    """Export all plans as CSV"""
    plans = db.query(NotfallPlan).all()
    
    output = io.StringIO()
    # Add BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        "ID", "Start", "Ende", "Benutzer ID", "Vorname", "Nachname", 
        "Telefon", "E-Mail", "Bestätigt", "Erstellt am", "Erstellt von"
    ])
    
    # Data
    for plan in plans:
        user = plan.user
        writer.writerow([
            plan.id,
            plan.start_date.strftime("%Y-%m-%d %H:%M") if plan.start_date else "",
            plan.end_date.strftime("%Y-%m-%d %H:%M") if plan.end_date else "",
            user.id if user else "",
            user.first_name if user else "",
            user.last_name if user else "",
            user.phone_number if user else "",
            user.email if user else "",
            "Ja" if plan.confirmed else "Nein",
            plan.created_at.strftime("%Y-%m-%d %H:%M") if plan.created_at else "",
            plan.created_by or ""
        ])
    
    output.seek(0)
    filename = f"notfallplan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/plans/pdf")
async def export_plans_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_export_access)
):
    """Export all plans as PDF"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    plans = db.query(NotfallPlan).order_by(NotfallPlan.start_date.desc()).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = 1 # Center
    
    elements.append(Paragraph("Notfallplan Export", title_style))
    elements.append(Paragraph(f"Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    data = [["Start", "Ende", "Name", "Telefon", "E-Mail", "Status", "Erstellt von"]]
    
    for plan in plans:
        user = plan.user
        start = plan.start_date.strftime("%d.%m.%Y %H:%M") if plan.start_date else "-"
        end = plan.end_date.strftime("%d.%m.%Y %H:%M") if plan.end_date else "-"
        name = f"{user.first_name} {user.last_name}" if user else "Unbekannt"
        phone = user.phone_number or "" if user else ""
        email = user.email or "" if user else ""
        status = "Bestätigt" if plan.confirmed else "Entwurf"
        creator = plan.created_by or "System"
        
        data.append([start, end, name, phone, email, status, creator])
        
    table = Table(data, colWidths=[90, 90, 120, 90, 150, 60, 80])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    filename = f"notfallplan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/audit")
async def export_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_export_access)
):
    """Export audit log as CSV"""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        "ID", "Zeitstempel", "Benutzer", "Aktion", "Tabelle", "Ziel-ID"
    ])
    
    # Data
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            log.username or "System",
            log.action,
            log.target_table,
            log.target_id or ""
        ])
    
    output.seek(0)
    filename = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
