from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime

def generate_certificate(student_name, lesson_title,
                         score, total, percentage):
    buffer = io.BytesIO()
    w, h   = landscape(A4)
    c      = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Background
    c.setFillColorRGB(0.98, 0.97, 0.94)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Outer border
    c.setStrokeColorRGB(0.78, 0.64, 0.18)
    c.setLineWidth(6)
    c.rect(20, 20, w-40, h-40, fill=0, stroke=1)

    c.setStrokeColorRGB(0.91, 0.76, 0.31)
    c.setLineWidth(2)
    c.rect(30, 30, w-60, h-60, fill=0, stroke=1)

    # Header background
    c.setFillColorRGB(0.10, 0.10, 0.18)
    c.rect(40, h-130, w-80, 90, fill=1, stroke=0)

    # Gold accent line
    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.rect(40, h-138, w-80, 8, fill=1, stroke=0)

    # Header text
    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(
        w/2, h-80,
        "DISASTER PREPAREDNESS AND RESPONSE EDUCATION SYSTEM"
    )

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        w/2, h-98,
        "Preparedness  •  Response  •  Education  •  Safety"
    )

    # Certificate title
    c.setFillColorRGB(0.10, 0.10, 0.18)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w/2, h-185, "CERTIFICATE")

    c.setFillColorRGB(0.78, 0.64, 0.18)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h-215, "OF  COMPLETION")

    # Decorative line
    c.setStrokeColorRGB(0.78, 0.64, 0.18)
    c.setLineWidth(1.5)
    c.line(w/2-180, h-230, w/2+180, h-230)

    # Certify text
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(w/2, h-260, "This is to certify that")

    # Student name
    c.setFillColorRGB(0.10, 0.10, 0.18)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(w/2, h-300, student_name)

    # Underline name
    name_width = c.stringWidth(student_name, "Helvetica-Bold", 32)
    c.setStrokeColorRGB(0.10, 0.10, 0.18)
    c.setLineWidth(1)
    c.line(w/2-name_width/2-10, h-308,
           w/2+name_width/2+10, h-308)

    # Has completed text
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(
        w/2, h-335,
        "has successfully completed the course on"
    )

    # Lesson title
    c.setFillColorRGB(0.91, 0.41, 0.18)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h-365, lesson_title)

    # Score boxes
    box_y  = h - 430
    boxes  = [
        ('Score',      f"{score}/{total}",          0.10, 0.10, 0.18),
        ('Percentage', f"{percentage:.1f}%",         0.91, 0.41, 0.18),
        ('Grade',
         'A+' if percentage >= 90 else
         'A'  if percentage >= 80 else
         'B'  if percentage >= 70 else 'C',           0.78, 0.64, 0.18),
        ('Status',     'PASSED',                     0.18, 0.63, 0.43),
    ]

    box_w   = 130
    total_w = len(boxes)*box_w + (len(boxes)-1)*20
    start_x = (w - total_w) / 2

    for i, (label, value, r, g, b) in enumerate(boxes):
        bx = start_x + i*(box_w+20)
        c.setFillColorRGB(r, g, b)
        c.roundRect(bx, box_y, box_w, 60, 8, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(bx+box_w/2, box_y+32, str(value))
        c.setFont("Helvetica", 9)
        c.drawCentredString(bx+box_w/2, box_y+14, label)

    # Signatures
    sig_y = h - 510

    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 10)
    date_str = datetime.now().strftime("%d %B %Y")
    c.drawCentredString(
        w/4, sig_y,
        f"Date of Completion: {date_str}"
    )

    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.5)
    c.line(w/4-100, sig_y-20, w/4+100, sig_y-20)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.10, 0.10, 0.18)
    c.drawCentredString(3*w/4, sig_y, "Authorized Signatory")
    c.line(3*w/4-100, sig_y-20, 3*w/4+100, sig_y-20)

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(
        3*w/4, sig_y-32,
        "Disaster Preparedness System"
    )

    # Footer
    c.setFillColorRGB(0.10, 0.10, 0.18)
    c.rect(40, 40, w-80, 28, fill=1, stroke=0)

    c.setFillColorRGB(0.91, 0.76, 0.31)
    c.setFont("Helvetica", 8)
    c.drawCentredString(
        w/2, 50,
        "This certificate is awarded in recognition of outstanding "
        "dedication to disaster preparedness education  "
        "•  Emergency: 112  |  Fire: 101  |  Ambulance: 102"
    )

    # Corner decorations
    gold    = (0.91, 0.76, 0.31)
    corners = [
        (50, 50), (w-50, 50),
        (50, h-50), (w-50, h-50)
    ]
    for cx, cy in corners:
        c.setFillColorRGB(*gold)
        c.circle(cx, cy, 8, fill=1, stroke=0)
        c.setFillColorRGB(0.10, 0.10, 0.18)
        c.circle(cx, cy, 4, fill=1, stroke=0)

    c.save()
    buffer.seek(0)
    return buffer