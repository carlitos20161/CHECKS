from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from num2words import num2words
import datetime
import base64
from reportlab.lib.utils import ImageReader
from PIL import Image

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
    
    # Draw company information and logo if available
    if check.company.logo:
        try:
            # Decode the base64 logo
            logo_data = base64.b64decode(check.company.logo)
            logo_stream = BytesIO(logo_data)
            logo_image = Image.open(logo_stream)
            
            # Resize logo to fit properly on check
            max_width = 1.5 * inch
            max_height = 0.75 * inch
            width, height = logo_image.size
            
            # Calculate aspect ratio to maintain proportions
            aspect = width / height
            if width > max_width:
                width = max_width
                height = width / aspect
            if height > max_height:
                height = max_height
                width = height * aspect
                
            # Save resized image to a BytesIO object
            resized_logo = BytesIO()
            logo_image.resize((int(width), int(height)), Image.LANCZOS).save(resized_logo, format=logo_image.format or 'PNG')
            resized_logo.seek(0)
            
            # Draw the logo
            c.drawImage(ImageReader(resized_logo), 4.5*inch, 5.8*inch, width=width, height=height)
            
            # Adjust company info position to be below logo
            c.setFont("Helvetica", 10)
            c.drawString(4.5*inch, 5.7*inch, check.company.name)
            c.drawString(4.5*inch, 5.5*inch, check.company.address)
            
        except Exception as e:
            # If there's an error with the logo, fall back to just text
            c.setFont("Helvetica", 10)
            c.drawString(4.5*inch, 5.7*inch, check.company.name)
            c.drawString(4.5*inch, 5.5*inch, check.company.address)
    else:
        # No logo, just draw the text
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
    
    # Draw pay breakdown if available
    if any([check.hours_worked, check.overtime_hours, check.holiday_hours]):
        c.setFont("Helvetica", 8)
        breakdown_y = 4.0*inch
        
        # Draw a lightweight box for the breakdown
        c.setFillColorRGB(0.95, 0.95, 0.95)  # Light gray
        c.rect(1.2*inch, breakdown_y - 0.4*inch, 2.5*inch, 0.45*inch, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)  # Back to black
        
        c.drawString(1.25*inch, breakdown_y, "PAY BREAKDOWN:")
        
        if check.hours_worked and check.pay_rate:
            regular_pay = float(check.hours_worked) * float(check.pay_rate)
            c.drawString(1.25*inch, breakdown_y - 0.15*inch, f"Regular: {check.hours_worked} hrs × ${float(check.pay_rate):.2f} = ${regular_pay:.2f}")
            
        if check.overtime_hours and check.overtime_rate:
            overtime_pay = float(check.overtime_hours) * float(check.overtime_rate)
            c.drawString(1.25*inch, breakdown_y - 0.25*inch, f"Overtime: {check.overtime_hours} hrs × ${float(check.overtime_rate):.2f} = ${overtime_pay:.2f}")
            
        if check.holiday_hours and check.holiday_rate:
            holiday_pay = float(check.holiday_hours) * float(check.holiday_rate)
            c.drawString(1.25*inch, breakdown_y - 0.35*inch, f"Holiday: {check.holiday_hours} hrs × ${float(check.holiday_rate):.2f} = ${holiday_pay:.2f}")
    
    # Draw signature line
    c.line(4*inch, 3.5*inch, 6.5*inch, 3.5*inch)
    c.setFont("Helvetica", 10)
    c.drawString(5*inch, 3.3*inch, "Authorized Signature")
    
    # Draw memo line with client info if available
    if check.client:
        if check.memo:
            memo_text = f"Memo: {check.memo} - Client: {check.client.name}"
        else:
            memo_text = f"Memo: Work for {check.client.name}"
    else:
        if check.memo:
            memo_text = f"Memo: {check.memo}"
        else:
            memo_text = f"Memo: Payment to {check.employee.title}"
    
    # Make sure memo text isn't too long for the check
    if len(memo_text) > 50:
        memo_text = memo_text[:47] + "..."
        
    c.drawString(1.2*inch, 3.3*inch, memo_text)
    
    # Save the PDF
    c.showPage()
    c.save()
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
