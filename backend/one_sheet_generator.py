from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def _draw_background(c, width, height):
    # Deep Charcoal Background
    c.setFillColorRGB(0.05, 0.05, 0.07)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Header Accent (Top gradient simulation)
    c.setFillColorRGB(0.08, 0.08, 0.1)
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)

    # Neon Cyan Header Line
    c.setFillColorRGB(0.02, 0.71, 0.83) # Accent Cyan
    c.rect(0, height - 100, width, 2, fill=True, stroke=False)

def _draw_header(c, data, height):
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 32)
    title_text = str(data.get('title', 'Untitled Track')).upper()
    c.drawString(40, height - 60, title_text)

    c.setFillColorRGB(0.6, 0.6, 0.7)
    c.setFont("Helvetica", 14)
    artist_text = f"BY {str(data.get('artist', 'UNKNOWN ARTIST')).upper()}"
    c.drawString(40, height - 85, artist_text)

def _draw_ai_sonic_footprint(c, data, width, start_y):
    y = start_y
    c.setFillColorRGB(0.66, 0.33, 0.97) # Accent Purple
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "AI SONIC FOOTPRINT")

    c.setStrokeColorRGB(0.2, 0.2, 0.25)
    c.line(40, y - 5, width - 40, y - 5)

    y -= 35
    # Column 1
    analysis_left = [
        ("BPM", f"{data.get('bpm', '0.0')} BPM"),
        ("KEY / SCALE", f"{data.get('key', 'Unknown')} {str(data.get('scale', '')).upper()}"),
        ("ENERGY", f"{int(float(data.get('energy', 0)) * 100)}% DENSITY"),
    ]

    # Column 2
    analysis_right = [
        ("PRIMARY MOOD", str(data.get('mood', 'N/A')).upper()),
        ("GENRE / STYLE", str(data.get('genre', 'N/A')).upper()),
        ("VOCALS", str(data.get('vocalPresence', 'N/A')).upper()),
    ]

    # Draw Columns
    curr_y = y
    for label, val in analysis_left:
        c.setFillColorRGB(0.4, 0.4, 0.5)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, curr_y, label)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, curr_y - 15, str(val))
        curr_y -= 45

    curr_y = y
    for label, val in analysis_right:
        c.setFillColorRGB(0.4, 0.4, 0.5)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(300, curr_y, label)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(300, curr_y - 15, str(val))
        curr_y -= 45

    return curr_y

def _draw_instrumentation(c, data, width, start_y):
    y = start_y - 20
    c.setFillColorRGB(0.02, 0.71, 0.83) # Accent Cyan
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "INSTRUMENTATION & PRODUCTION")
    c.setStrokeColorRGB(0.2, 0.2, 0.25)
    c.line(40, y - 5, width - 40, y - 5)

    y -= 25
    c.setFillColorRGB(0.8, 0.8, 0.9)
    c.setFont("Helvetica", 11)
    instruments = data.get('instruments', 'N/A')
    if isinstance(instruments, list): instruments = ", ".join(instruments)
    c.drawString(40, y, str(instruments).upper())

    return y

def _draw_sync_and_licensing(c, data, width, start_y):
    y = start_y - 50
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "SYNC & LICENSING")
    c.setStrokeColorRGB(0.2, 0.2, 0.25)
    c.line(40, y - 5, width - 40, y - 5)

    y -= 30
    sync_fields = [
        ("STATUS", "ONE-STOP" if data.get('oneStop') else "CLEARANCE REQUIRED"),
        ("PUBLISHER", data.get('publisher', 'N/A')),
        ("WRITERS", data.get('composer', 'N/A')),
        ("ISRC", data.get('isrc', 'PENDING')),
    ]

    for label, val in sync_fields:
        c.setFillColorRGB(0.4, 0.4, 0.5)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, label)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica", 11)
        c.drawString(140, y, str(val))
        y -= 25

    return y

def _draw_comments_and_story(c, data, width, start_y):
    y = start_y - 10
    c.setFillColorRGB(0.4, 0.4, 0.5)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y, "SYNC TERMS / STORY")
    y -= 15
    c.setFillColorRGB(0.7, 0.7, 0.8)
    c.setFont("Helvetica-Oblique", 10)

    # Word wrap naive
    comment_text = data.get('comments', 'No additional terms provided for this submission.')
    words = str(comment_text).split(' ')
    line = ""
    for word in words:
        if (len(line + word) * 5) > (width - 80):
            c.drawString(40, y, line)
            line = word + " "
            y -= 15
        else:
            line += word + " "
    c.drawString(40, y, line)

    return y

def _draw_footer(c, data, width):
    c.setFillColorRGB(0.08, 0.08, 0.1)
    c.rect(0, 0, width, 80, fill=True, stroke=False)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 50, "POINT OF CONTACT")

    c.setFillColorRGB(0.02, 0.71, 0.83) # Cyan
    c.setFont("Helvetica", 10)
    contact_str = f"{data.get('contactName', 'N/A')} // {data.get('contactEmail', 'N/A')} // {data.get('contactPhone', '')}"
    c.drawString(40, 32, contact_str.upper())

    # Branding
    c.setFillColorRGB(0.4, 0.4, 0.5)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(width - 150, 32, "GENERATED BY RESONANTCRAB")

def generate_one_sheet(file_path: str, data: dict, output_path: str):
    """
    Generates a premium, cinematic Dark Mode One-Sheet PDF.
    """
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # --- BACKGROUND ---
        _draw_background(c, width, height)

        # --- HEADER ---
        _draw_header(c, data, height)
        
        # --- SECTION: AI SONIC FOOTPRINT ---
        y = _draw_ai_sonic_footprint(c, data, width, height - 160)

        # --- SECTION: INSTRUMENTATION & PRODUCTION ---
        y = _draw_instrumentation(c, data, width, y)

        # --- SECTION: SYNC & LICENSING ---
        y = _draw_sync_and_licensing(c, data, width, y)

        # --- COMMENTS / STORY ---
        y = _draw_comments_and_story(c, data, width, y)

        # --- FOOTER ---
        _draw_footer(c, data, width)

        c.save()
        return True
    except Exception as e:
        print(f"Error generating Cinematic One-Sheet: {e}")
        return False
