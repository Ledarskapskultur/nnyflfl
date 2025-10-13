from reportlab.lib.colors import HexColor, Color, black
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import textwrap
from io import BytesIO
from datetime import datetime

def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Bakgrund (äggskalsvit) och bas
    EGGSHELL = "#FAF7F0"
    pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0, 0, w, h, fill=1, stroke=0)
    pdf.setFillColor(black)
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    margin = 50
    y = h - 60

    # H1 + tidsstämpel
    pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, y, title)
    pdf.setFont("Helvetica", 9); pdf.drawRightString(w - margin, y + 4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
    y -= 28

    # Kontaktuppgifter
    pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    row = [
        f"Unikt id: {contact.get('Unikt id','')}",
        f"Namn: {contact.get('Namn','')}",
        f"Företag: {contact.get('Företag','')}",
        f"Telefon: {contact.get('Telefon','')}",
        f"E-post: {contact.get('E-post','')}",
    ]
    one_line = "   |   ".join(row)
    if len(one_line) > 110:
        mid = len(row) // 2
        pdf.drawString(margin, y, "   |   ".join(row[:mid])); y -= 14
        pdf.drawString(margin, y, "   |   ".join(row[mid:])); y -= 8
    else:
        pdf.drawString(margin, y, one_line); y -= 14

    # Hjälpare
    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage()
            pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0, 0, w, h, fill=1, stroke=0)
            pdf.setFillColor(black)
            pdf.setFont("Helvetica", 9); pdf.drawString(margin, h - 40, title)
            y = h - 60

    # Färger för barer
    bar_bg = Color(0.91, 0.92, 0.94)       # #E9ECEF
    col_chef = Color(0.30, 0.69, 0.31)     # #4CAF50
    col_over = Color(0.96, 0.65, 0.15)     # #F5A524
    col_med  = Color(0.23, 0.51, 0.96)     # #3B82F6

    # Layout 68/32 – samma som webben
    content_w = w - 2 * margin
    left_w    = content_w * 0.68
    right_w   = content_w - left_w
    right_x   = margin + left_w

    for s in sections:
        ensure(40)
        # Rubrik
        pdf.setFont("Helvetica-Bold", 19 * 0.75)   # ~14 pt motsv. H2 på web
        pdf.drawString(margin, y, s["title"])
        y -= 20

        # Startnivå för denna sektion i båda spalter
        section_top_y = y

        # Höger: Rita ett "kort" (vit ruta med kant) med tre barer
        card_pad  = 10
        card_w    = right_w - 10         # lite inner-marg
        # Räkna ut dynamisk höjd: (3 roller) * (etikett 12 + bar 8 + gap 14) + "Max"-rad + inner padding
        per_role  = 12 + 8 + 14
        card_h    = card_pad + 3 * per_role + 10 + card_pad
        card_y    = section_top_y - card_h + 6   # +6 för att linjera lite ned från H2 (som webben gör)

        # Kortets box
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setStrokeColor(HexColor("#D1D5DB"))   # kant
        try:
            pdf.roundRect(right_x + 5, card_y, card_w, card_h, 12, stroke=1, fill=1)
        except Exception:
            pdf.rect(right_x + 5, card_y, card_w, card_h, stroke=1, fill=1)
        pdf.setFillColor(black)

        # Innehållet i kortet
        inner_x = right_x + 5 + card_pad
        cur_y   = card_y + card_h - card_pad - 4

        # Tre roller i ordning
        roles = [("Chef",      "chef",      col_chef),
                 ("Överordnad chef", "overchef", col_over),
                 ("Medarbetare",     "medarbetare", col_med)]

        pdf.setFont("Helvetica", 10)
        for label, key, col in roles:
            val = int(results_map.get(s["key"], {}).get(key, 0))
            mx  = int(s.get("max", 0))

            # Etikett: "Chef: X poäng"
            pdf.drawString(inner_x, cur_y, f"{label}: {val} poäng")
            cur_y -= 12

            # Bar
            bar_w = card_w - 2 * card_pad
            bar_h = 10
            pdf.setFillColor(bar_bg); pdf.rect(inner_x, cur_y, bar_w, bar_h, fill=1, stroke=0)
            fill_w = 0 if mx == 0 else bar_w * (val / mx)
            pdf.setFillColor(col); pdf.rect(inner_x, cur_y, fill_w, bar_h, fill=1, stroke=0)
            pdf.setFillColor(black)
            cur_y -= 14

        # "Max: N poäng" längst ner i kortet
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(inner_x, card_y + card_pad, f"Max: {int(s.get('max', 0))} poäng")

        # Vänster: brödtext inom 68 %
        pdf.setFont("Helvetica", 11)
        y_left = section_top_y
        approx_chars = max(40, int(95 * (left_w / content_w)))  # enkel wrap-adaption
        for para in s["text"].split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                ensure(16); pdf.drawString(margin, y_left, ln); y_left -= 16
            y_left -= 4

        # Nästa sektion startar under den lägsta punkten (vänster text eller kortets nederkant)
        y = min(y_left, card_y) - 16

    pdf.showPage(); pdf.save(); buf.seek(0); return buf.getvalue()
