from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64

def generate_clean_check(check):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    left = 0.75 * inch
    right = 7.75 * inch
    top = 10.25 * inch
    line_gap = 14

    # Company logo or name
    if check.company.logo:
        try:
            logo_data = base64.b64decode(check.company.logo)
            logo_image = ImageReader(BytesIO(logo_data))
            c.drawImage(logo_image, left, top - 20, width=100, height=40, mask='auto')
        except:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left, top, check.company.name)
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, top, check.company.name)

    c.setFont("Helvetica", 10)
    c.drawString(left, top - line_gap, check.company.address or "")

    # Bank & check number
    c.setFont("Helvetica-Bold", 11)
    c.drawString(4.5 * inch, top, check.bank.name)
    c.drawRightString(right, top, f"Check #: {check.check_number}")

    # Date
    c.setFont("Helvetica", 10)
    c.drawString(6.2 * inch, top - 35, "DATE")
    c.drawRightString(right, top - 35, check.date.strftime("%m/%d/%Y"))

    # Pay to the order of
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, top - 65, "PAY TO THE ORDER OF")
    c.setFont("Helvetica", 11)
    c.drawString(left + 130, top - 65, check.employee.name)

    # Amount box
    c.setFont("Helvetica-Bold", 12)
    c.rect(6.25 * inch, top - 78, 1.2 * inch, 20)
    c.drawCentredString(6.85 * inch, top - 73, f"${check.amount:,.2f}")

    # Amount in words
    from num2words import num2words
    amount_words = num2words(check.amount, to='currency', lang='en').replace("euro", "dollars").capitalize()
    c.setFont("Helvetica", 10)
    c.drawString(left, top - 100, f"{amount_words} dollars")

    # Memo and client info
    c.setFont("Helvetica", 10)
    memo = check.memo or (f"Work for {check.client.name}" if check.client else "Work completed")
    c.drawString(left, top - 130, f"MEMO: {memo}")
    if check.client:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(left, top - 145, f"Client: {check.client.name}")

    # Signature line
    c.line(5.5 * inch, top - 127, right, top - 127)
    c.setFont("Helvetica", 8)
    c.drawString(6.0 * inch, top - 140, "AUTHORIZED SIGNATURE")

    # Breakdown
    y = top - 170
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Description")
    c.drawRightString(5.5 * inch, y, "Amount")
    y -= 12
    c.setFont("Helvetica", 9)

    if check.hours_worked and check.pay_rate:
        c.drawString(left, y, f"Regular Hours ({check.hours_worked} × ${check.pay_rate:.2f})")
        c.drawRightString(5.5 * inch, y, f"${check.hours_worked * check.pay_rate:.2f}")
        y -= 12

    if check.overtime_hours and check.overtime_rate:
        c.drawString(left, y, f"Overtime Hours ({check.overtime_hours} × ${check.overtime_rate:.2f})")
        c.drawRightString(5.5 * inch, y, f"${check.overtime_hours * check.overtime_rate:.2f}")
        y -= 12

    if check.holiday_hours and check.holiday_rate:
        c.drawString(left, y, f"Holiday Hours ({check.holiday_hours} × ${check.holiday_rate:.2f})")
        c.drawRightString(5.5 * inch, y, f"${check.holiday_hours * check.holiday_rate:.2f}")
        y -= 12

    # MICR line
    c.setFont("Courier-Bold", 12)
    micr = f"C {check.check_number:0>6} C {check.bank.routing_number} A {check.bank.account_number} A"
    c.drawCentredString(width / 2, 0.75 * inch, micr)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    left = 0.75 * inch
    top = 10.25 * inch

    # === Company Logo or Name (Paying Company) ===
    if check.company.logo:
        try:
            logo_data = base64.b64decode(check.company.logo)
            logo_image = ImageReader(BytesIO(logo_data))
            c.drawImage(logo_image, left, top - 20, width=100, height=40, mask='auto')
        except:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left, top, check.company.name)
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, top, check.company.name)

    c.setFont("Helvetica", 10)
    c.drawString(left, top - 14, check.company.address or "")

    # === Bank Info ===
    c.setFont("Helvetica-Bold", 11)
    c.drawString(4.5 * inch, top, check.bank.name)
    c.drawRightString(7.6 * inch, top, f"Check #: {check.check_number}")

    # === Date ===
    c.setFont("Helvetica", 10)
    c.drawRightString(7.0 * inch, top - 35, "DATE")
    c.drawString(7.1 * inch, top - 35, check.date.strftime("%m/%d/%Y"))

    # === Payee Line ===
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, top - 65, "PAY TO THE ORDER OF")
    c.setFont("Helvetica", 11)
    c.drawString(left + 130, top - 65, check.employee.name)

    # === Amount Box ===
    c.setFont("Helvetica-Bold", 12)
    c.rect(6.25 * inch, top - 78, 1.2 * inch, 20)
    c.drawCentredString(6.85 * inch, top - 73, f"${check.amount:,.2f}")

    # === Amount in Words ===
    from num2words import num2words
    amount_words = num2words(check.amount, to='currency', lang='en').replace("euro", "dollars").capitalize()
    c.setFont("Helvetica", 10)
    c.drawString(left, top - 100, f"{amount_words} ------------------------ DOLLARS")

    # === Memo and Client Info ===
    c.setFont("Helvetica", 10)
    memo = check.memo or f"Work for {check.client.name}" if check.client else "Work completed"
    c.drawString(left, top - 130, f"MEMO {memo}")
    if check.client:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(left, top - 145, f"Client: {check.client.name}")

    c.line(5.5 * inch, top - 127, 7.8 * inch, top - 127)
    c.setFont("Helvetica", 8)
    c.drawString(6.0 * inch, top - 140, "AUTHORIZED SIGNATURE")

    # === Payment Breakdown Section ===
    y = top - 170
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Description")
    c.drawString(left + 250, y, "Amount")
    c.setFont("Helvetica", 9)
    y -= 12

    if check.hours_worked and check.pay_rate:
        c.drawString(left, y, f"Regular Hours ({check.hours_worked} × ${check.pay_rate:.2f})")
        c.drawRightString(left + 300, y, f"${check.hours_worked * check.pay_rate:.2f}")
        y -= 12

    if check.overtime_hours and check.overtime_rate:
        c.drawString(left, y, f"Overtime ({check.overtime_hours} × ${check.overtime_rate:.2f})")
        c.drawRightString(left + 300, y, f"${check.overtime_hours * check.overtime_rate:.2f}")
        y -= 12

    if check.holiday_hours and check.holiday_rate:
        c.drawString(left, y, f"Holiday ({check.holiday_hours} × ${check.holiday_rate:.2f})")
        c.drawRightString(left + 300, y, f"${check.holiday_hours * check.holiday_rate:.2f}")
        y -= 12

    # === MICR Line ===
    c.setFont("Courier-Bold", 12)
    micr = f"C {check.check_number:0>6} C {check.bank.routing_number} A {check.bank.account_number} A"
    c.drawString(left + 40, 0.75 * inch, micr)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
