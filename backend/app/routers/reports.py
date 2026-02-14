from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/generate")
def generate_inventory_report(db: Session = Depends(get_db)):
    # 1. Fetch Data
    products = db.query(Product).all()
    
    # 2. Create a memory buffer for the PDF (instead of saving to disk)
    buffer = io.BytesIO()
    
    # 3. Setup the PDF Document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # --- TITLE --
    title = Paragraph(f"ABC Company Ltd.<br/>Inventory Report - {datetime.now().strftime('%Y-%m-%d')}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # --- PREPARE TABLE DATA ---
    # Header Row
    data = [["Product Name", "Stock", "Unit", "Cost Price", "Total Value"]]
    
    grand_total_value = 0.0
    
    for p in products:
        stock_value = p.quantity * p.cost_price
        grand_total_value += stock_value
        
        # Add Row
        data.append([
            p.name_english,  # Using English to avoid font issues with Nepali
            f"{p.quantity}",
            p.unit,
            f"Rs. {p.cost_price}",
            f"Rs. {stock_value}"
        ])
        
    # Add Grand Total Row
    data.append(["", "", "", "GRAND TOTAL:", f"Rs. {grand_total_value}"])
    
    # --- CREATE TABLE STYLE ---
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight Total Row
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    
    elements.append(table)
    
    # 4. Build PDF
    doc.build(elements)
    
    # 5. Prepare buffer for download
    buffer.seek(0)
    
    # 6. Return as a Downloadable File
    headers = {
        'Content-Disposition': f'attachment; filename="Inventory_Report_{datetime.now().strftime("%Y%m%d")}.pdf"'
    }
    return StreamingResponse(buffer, headers=headers, media_type='application/pdf')