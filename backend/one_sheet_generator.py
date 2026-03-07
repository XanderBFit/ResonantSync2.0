from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os

def generate_one_sheet(file_path: str, data: dict, output_path: str):
    """
    Generates a sleek, professional One-Sheet PDF with track details,
    Cyanite-level mood/genre analysis, and Sync points.
    """
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Background Layout (Gradient simulation with simple dark box for header)
        c.setFillColorRGB(0.04, 0.04, 0.05)
        c.rect(0, height - 120, width, 120, fill=True, stroke=False)
        
        # Header text
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(40, height - 60, data.get('title', 'Untitled Track'))
        
        c.setFillColorRGB(0.7, 0.7, 0.7)
        c.setFont("Helvetica", 16)
        c.drawString(40, height - 90, f"by {data.get('artist', 'Unknown Artist')}")
        
        # Section: AI Audio Analysis
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 160, "Track Analysis Profile (Cyanite AI)")
        
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(40, height - 168, width - 40, height - 168)
        
        c.setFont("Helvetica", 12)
        y = height - 190
        
        analysis_fields = [
            ("BPM", str(data.get('bpm', ''))),
            ("Key", data.get('key', '')),
            ("Primary Genre", data.get('genre', '')),
            ("Mood Profile", data.get('mood', '')),
            ("Energy Dynamics", data.get('energy', '')),
            ("Vocal Presence", data.get('vocalPresence', '')),
            ("Instrumentation", data.get('instruments', ''))
        ]
        
        for label, val in analysis_fields:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, f"{label}:")
            c.setFont("Helvetica", 12)
            c.drawString(180, y, val)
            y -= 25

        # Section: Sync & Publishing Details
        y -= 20
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, y, "Sync & Licensing Information")
        c.line(40, y - 8, width - 40, y - 8)
        
        y -= 30
        sync_fields = [
            ("Declared One-Stop", "YES" if data.get('oneStop') else "NO"),
            ("Composers / Splits", data.get('composer', '')),
            ("Publishing", data.get('publisher', '')),
            ("ISRC", data.get('isrc', '')),
            ("Grouping / Sounds Like", data.get('grouping', '')),
        ]
        
        for label, val in sync_fields:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, f"{label}:")
            c.setFont("Helvetica", 12)
            text_val = str(val)[:75] + "..." if len(str(val)) > 75 else str(val)
            c.drawString(180, y, text_val)
            y -= 25

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Sync Terms / Story:")
        y -= 20
        c.setFont("Helvetica", 10)
        
        # Word wrap naive
        comment_text = data.get('comments', '')
        words = comment_text.split(' ')
        line = ""
        for word in words:
            if len(line + word) * 5 > (width - 80): # Approx width calc
                c.drawString(40, y, line)
                line = word + " "
                y -= 15
            else:
                line += word + " "
        c.drawString(40, y, line)
        
        # Footer / Contact
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(0, 0, width, 80, fill=True, stroke=False)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 50, "Contact Details")
        c.setFont("Helvetica", 12)
        contact_str = f"{data.get('contactName', '')} | {data.get('contactEmail', '')} | {data.get('contactPhone', '')}"
        c.drawString(40, 30, contact_str)

        c.save()
        return True
    except Exception as e:
        print(f"Error generating One-Sheet: {e}")
        return False
