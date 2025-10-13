from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color, black
import textwrap
from io import BytesIO

def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    EGGSHELL = "#FAF7F0"

    def paint_bg():
        pdf.setFillColor(HexColor(EGGSHELL))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        pdf.setFillColor(black)

    paint_bg()
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    margin = 50
    y = h - 60

    # H1 (ingen tidsstämpel längre)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(margin, y, title)
    y -= 28

    # Kontaktuppgifter – två rader i specificerad ordning
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y, "Kontaktuppgifter")
    y -= 14
    pdf.setFont("Helvetica", 10)

    line1 = "   |   ".join([
        f"Namn: {contact.get('Namn','')}",
        f"Företag: {contact.get('Företag','')}",
        f"Telefon: {contact.get('Telefon','')}",
    ])
    line2 = "   |   ".join([
        f"E-post: {contact.get('E-post','')}",
        f"Unikt id: {contact.get('Unikt id','')}",
    ])
    pdf.drawString(margin, y, line1); y -= 14
    pdf.drawString(margin, y, line2); y -= 16  # extra luft under kontaktraden

    # Flytta ner så att första sektionens rubrik startar där brödtextflödet upplevs börja
    y -= 8  # liten buffert så "Aktivt lyssnande" hamnar lägre/mer i nivå med textytan

    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage()
            paint_bg()
            # Visa H1 även på nya sidan för konsekvent layout
            yy = h - 60
            pdf.setFont("Helvetica-Bold", 22)
            pdf.drawString(margin, yy, title)
            y = yy - 28

            # Återupprepa "Kontaktuppgifter" inte – nästa sidor innehåller bara sektioner

    # Färger för bars (samma som webben)
    bar_bg  = Color(0.91, 0.92, 0.94)    # #E9ECEF
    col_chef = Color(0.30, 0.69, 0.31)   # #4CAF50
    col_over = Color(0.96, 0.65, 0.15)   # #F5A524
    col_med  = Color(0.23, 0.51, 0.96)   # #3B82F6

    # 68/32 kolumnlayout
    content_w = w - 2*margin
    left_w    = content_w * 0.68
    right_w   = content_w - left_w
    right_x   = margin + left_w

    for s in sections:
        # S idbrytning precis före "Målinriktning"
        if s.get("title") == "Målinriktning":
            pdf.showPage()
            paint_bg()
            yy = h - 60
            pdf.setFont("Helvetica-Bold", 22)
            pdf.drawString(margin, yy, title)
            y = yy - 28

        ensure(40)
        # H2
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y, s["title"])
        y -= 20

        # Topp för denna sektion (för att linjera kortet med brödtextens topp)
        section_top = y

        # Höger – resultatkort
        card_pad = 10
        card_w   = right_w - 10
        per_role = 12 + 10 + 14   # etikett + bar + mellanrum
        card_h   = card_pad + 3*per_role + 10 + card_pad
        card_y   = section_top - card_h + 6  # lite ned från H2, så kortet linjerar med brödtextens start

        # Kort-bakgrund (vit med tunn kant)
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setStrokeColor(HexColor("#D1D5DB"))
        try:
            pdf.roundRect(right_x + 5, card_y, card_w, card_h, 12, stroke=1, fill=1)
        except Exception:
            pdf.rect(right_x + 5, card_y, card_w, card_h, stroke=1, fill=1)
        pdf.setFillColor(black)

        inner_x = right_x + 5 + card_pad
        cy      = card_y + card_h - card_pad - 4

        roles = [("Chef", "chef", col_chef),
                 ("Överordnad chef", "overchef", col_over),
                 ("Medarbetare", "medarbetare", col_med)]

        pdf.setFont("Helvetica", 10)
        for label, key, col in roles:
            val = int(results_map.get(s["key"], {}).get(key, 0))
            mx  = int(s.get("max", 0))
            pdf.drawString(inner_x, cy, f"{label}: {val} poäng"); cy -= 12
            bar_w = card_w - 2*card_pad; bar_h = 10
            pdf.setFillColor(bar_bg); pdf.rect(inner_x, cy, bar_w, bar_h, fill=1, stroke=0)
            fill_w = 0 if mx == 0 else bar_w * (val / mx)
            pdf.setFillColor(col); pdf.rect(inner_x, cy, fill_w, bar_h, fill=1, stroke=0)
            pdf.setFillColor(black); cy -= 14
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(inner_x, card_y + card_pad, f"Max: {int(s.get('max',0))} poäng")

        # Vänster – brödtext (wrap inom vänsterspalt)
        pdf.setFont("Helvetica", 11)
        y_left = section_top
        approx_chars = max(40, int(95 * (left_w / content_w)))
        for para in str(s.get("text","")).split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                ensure(16); pdf.drawString(margin, y_left, ln); y_left -= 16
            y_left -= 4

        # Nästa sektion under lägsta punkt
        y = min(y_left, card_y) - 16

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()
