from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO
from num2words import num2words
import datetime

def generate_check_pdf(check):
    """
    Generate a PDF representation of the check.
    
    Args:
        check: Check model instance
    
    Returns:
        PDF data as bytes
    """
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set font for the entire document
    c.setFont("Helvetica", 12)
    
    # Draw check border
    c.rect(1*inch, 3*inch, 6.5*inch, 3*inch, stroke=1, fill=0)
    
    # Draw bank information
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.2*inch, 5.7*inch, check.bank.name)
    c.setFont("Helvetica", 10)
    c.drawString(1.2*inch, 5.5*inch, f"Routing: {check.bank.routing_number}")
    c.drawString(1.2*inch, 5.3*inch, f"Account: {check.bank.account_number}")
    
    # Draw company information
    c.setFont("Helvetica", 10)
    c.drawString(4.5*inch, 5.7*inch, check.company.name)
    c.drawString(4.5*inch, 5.5*inch, check.company.address)
    
    # Draw check number
    c.setFont("Helvetica-Bold", 12)
    c.drawString(6*inch, 5*inch, f"Check No: {check.check_number}")
    
    # Draw date
    formatted_date = check.date.strftime("%B %d, %Y")
    c.drawString(6*inch, 4.7*inch, f"Date: {formatted_date}")
    
    # Draw pay to line
    c.setFont("Helvetica", 12)
    c.drawString(1.2*inch, 4.5*inch, "Pay to the order of:")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3*inch, 4.5*inch, check.employee.name)
    
    # Draw amount boxes
    c.setFont("Helvetica-Bold", 12)
    c.drawString(6*inch, 4.5*inch, f"${check.amount:.2f}")
    
    # Draw amount in words
    amount_in_words = num2words(float(check.amount), lang='en')
    c.setFont("Helvetica", 11)
    c.drawString(1.2*inch, 4.2*inch, f"{amount_in_words.capitalize()} dollars and {int(check.amount * 100) % 100}/100")
    
    # Draw signature line
    c.line(4*inch, 3.5*inch, 6.5*inch, 3.5*inch)
    c.setFont("Helvetica", 10)
    c.drawString(5*inch, 3.3*inch, "Authorized Signature")
    
    # Draw memo line
    c.drawString(1.2*inch, 3.3*inch, f"Memo: Payment to {check.employee.title}")
    
    # Save the PDF
    c.showPage()
    c.save()
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
