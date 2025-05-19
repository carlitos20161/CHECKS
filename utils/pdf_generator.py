from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import base64
import os
from num2words import num2words

# === MICR Font Registration ===
micr_font_path = os.path.join(os.path.dirname(__file__), "CovixMICRU copy.ttf")
MICR_REGISTERED = False
if os.path.exists(micr_font_path):
    try:
        pdfmetrics.registerFont(TTFont("MICR", micr_font_path))
        MICR_REGISTERED = True
    except Exception as e:
        print("⚠️ Failed to register MICR font:", e)

def generate_clean_check(check):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    left = 0.75 * inch
    right = 7.75 * inch
    top = 10.25 * inch

    # === Company Logo + Name & Address ===
    logo_width = 100
    logo_height = 40
    text_x = left + logo_width + 10
    text_y = top - logo_height / 2 + 10

    if check.company.logo:
        try:
            logo_data = base64.b64decode(check.company.logo)
            logo_image = ImageReader(BytesIO(logo_data))
            c.drawImage(logo_image, left, top - logo_height + 10, width=logo_width, height=logo_height, mask='auto')

            c.setFont("Helvetica-Bold", 12)
            c.drawString(text_x, text_y, check.company.name)
            c.setFont("Helvetica", 10)
            c.drawString(text_x, text_y - 14, check.company.address or "")
        except:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left, top, check.company.name)
            c.setFont("Helvetica", 10)
            c.drawString(left, top - 14, check.company.address or "")
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, top, check.company.name)
        c.setFont("Helvetica", 10)
        c.drawString(left, top - 14, check.company.address or "")

    # === Bank & Just Number (no label) ===
    c.setFont("Helvetica-Bold", 11)
    c.drawString(4.5 * inch, top, check.bank.name)
    c.drawRightString(right, top, str(check.check_number))

    # === Date + VOID NOTICE ===
    c.setFont("Helvetica", 10)
    c.drawString(6.2 * inch, top - 35, "DATE")
    c.drawRightString(right, top - 35, check.date.strftime("%m/%d/%Y"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(right, top - 48, "VOID AFTER 90 DAYS")

    # === Payee ===
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, top - 65, "PAY TO THE ORDER OF")
    c.setFont("Helvetica", 11)
    c.drawString(left + 130, top - 65, check.employee.name)
    c.line(left + 125, top - 67, 5.2 * inch, top - 67)

    # === Amount Box ===
    c.setFont("Helvetica-Bold", 12)
    c.rect(6.25 * inch, top - 78, 1.2 * inch, 20)
    c.drawCentredString(6.85 * inch, top - 73, f"${check.amount:,.2f}")

    # === Amount in Words ===
    amount_words = num2words(check.amount, to='currency', lang='en').replace("euro", "dollars").capitalize()
    c.setFont("Helvetica", 10)
    c.drawString(left, top - 100, f"{amount_words} dollars")
    c.line(left, top - 102, right, top - 102)

    # === Memo and Client Info ===
    c.setFont("Helvetica", 10)
    memo = check.memo or (f"Work for {check.client.name}" if check.client else "Work completed")
    c.drawString(left, top - 130, f"MEMO: {memo}")
    if check.client:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(left, top - 145, f"Client: {check.client.name}")

    # === Signature Line ===
    c.line(5.5 * inch, top - 127, right, top - 127)
    c.setFont("Helvetica", 8)
    c.drawString(6.0 * inch, top - 140, "AUTHORIZED SIGNATURE")

    # === MICR Line ===
    if MICR_REGISTERED:
        c.setFont("MICR", 12)
    else:
        c.setFont("Courier-Bold", 12)

    micr = f"C {check.check_number:0>6} C {check.bank.routing_number} A {check.bank.account_number} A"
    c.drawCentredString(width / 2, top - 160, micr)

    # === Breakdown Header Row ===
    y = top - 175
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, check.employee.name)  # Name on left
    c.drawRightString(right, y, str(check.check_number))  # Check number far right
    y -= 12

    # === Breakdown Labels ===
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Description")
    c.drawRightString(5.5 * inch, y, "Amount")
    y -= 12
    c.setFont("Helvetica", 9)

    # === Breakdown Rows ===
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

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
