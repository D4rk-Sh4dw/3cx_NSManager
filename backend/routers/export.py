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
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_export_access)
):
    """Export plans as CSV, optionally filtered by month/year"""
    query = db.query(NotfallPlan)
    
    start_of_period = None
    end_of_period = None

    if month and year:
        # Create date range for the selected month
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_of_period = datetime(year, month, 1)
        end_of_period = datetime(year, month, last_day, 23, 59, 59)
        
        # Filter plans that overlap with the selected month
        # overlap logic: start < end_of_period AND end > start_of_period
        query = query.filter(
            NotfallPlan.start_date <= end_of_period,
            NotfallPlan.end_date >= start_of_period
        )
        
    plans = query.all()
    
    # Calculate days per user if filtered
    user_days = {}
    if start_of_period and end_of_period:
        all_plans_in_period = plans # Since we already filtered
        for plan in all_plans_in_period:
            if not plan.user_id:
                continue
                
            # Calculate overlap duration in days
            # Intersect plan interval [p_start, p_end] with period interval [m_start, m_end]
            p_start = max(plan.start_date, start_of_period)
            p_end = min(plan.end_date, end_of_period)
            
            if p_start < p_end:
                duration = (p_end - p_start).days + 1 # +1 to include the partial day effectively as a day of duty? 
                # Actually, let's look at how "days" are usually counted. 
                # If a shift is 1 week (Monday to Monday), it's 7 days.
                # If we purely do diff, Monday 00:00 to Monday 00:00 is exactly 7.0 days.
                # Let's count full 24h periods or just the raw difference in days.
                # User asked for "wieviele tage ... geleistet hat".
                # Let's count the number of distinct days touched or just sum the duration.
                # Simple approach: (end - start).total_seconds() / 86400.
                # But typically shifts might be cleaner. Let's stick to days difference.
                days = (p_end - p_start).total_seconds() / (24 * 3600)
                user_days[plan.user_id] = user_days.get(plan.user_id, 0) + days

    output = io.StringIO()
    # Add BOM for Excel compatibility
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    
    headers = [
        "ID", "Start", "Ende", "Benutzer ID", "Vorname", "Nachname", 
        "Telefon", "E-Mail", "Bestätigt", "Erstellt am", "Erstellt von"
    ]
    if month and year:
        headers.append("Tage im Zeitraum")

    writer.writerow(headers)
    
    # Data
    for plan in plans:
        user = plan.user
        row = [
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
        ]
        
        if month and year:
            days = 0
            if user:
                 days = user_days.get(user.id, 0)
            row.append(f"{days:.2f}")

        writer.writerow(row)
    
    output.seek(0)
    filename_part = f"_{year}_{month}" if month and year else ""
    filename = f"notfallplan_export{filename_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/plans/pdf")
async def export_plans_pdf(
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_export_access)
):
    """Export plans as PDF, optionally filtered"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    query = db.query(NotfallPlan)
    
    start_of_period = None
    end_of_period = None

    if month and year:
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_of_period = datetime(year, month, 1)
        end_of_period = datetime(year, month, last_day, 23, 59, 59)
        query = query.filter(
            NotfallPlan.start_date <= end_of_period,
            NotfallPlan.end_date >= start_of_period
        )

    plans = query.order_by(NotfallPlan.start_date.desc()).all()
    
    # Calculate days per user if filtered
    user_days = {}
    if start_of_period and end_of_period:
        for plan in plans:
            if not plan.user_id:
                continue
            p_start = max(plan.start_date, start_of_period)
            p_end = min(plan.end_date, end_of_period)
            if p_start < p_end:
                days = (p_end - p_start).total_seconds() / (24 * 3600)
                user_days[plan.user_id] = user_days.get(plan.user_id, 0) + days

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = 1 # Center
    
    title_text = "Notfallplan Export"
    if month and year:
        title_text += f" - {month:02d}/{year}"
        
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    header = ["Start", "Ende", "Name", "Telefon", "E-Mail", "Status", "Erstellt von"]
    if month and year:
        header.append("Tage")
        
    data = [header]
    
    for plan in plans:
        user = plan.user
        start = plan.start_date.strftime("%d.%m.%Y %H:%M") if plan.start_date else "-"
        end = plan.end_date.strftime("%d.%m.%Y %H:%M") if plan.end_date else "-"
        name = f"{user.first_name} {user.last_name}" if user else "Unbekannt"
        phone = user.phone_number or "" if user else ""
        email = user.email or "" if user else ""
        status = "Bestätigt" if plan.confirmed else "Entwurf"
        creator = plan.created_by or "System"
        
        row = [start, end, name, phone, email, status, creator]
        
        if month and year:
            days = 0
            if user:
                days = user_days.get(user.id, 0)
            row.append(f"{days:.1f}")
            
        data.append(row)
        
    col_widths = [90, 90, 120, 90, 150, 60, 80]
    if month and year:
        col_widths.append(40) # Width for 'Tage' column
        
    table = Table(data, colWidths=col_widths)
    
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
    filename_part = f"_{year}_{month}" if month and year else ""
    filename = f"notfallplan_export{filename_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
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
