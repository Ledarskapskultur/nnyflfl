from io import BytesIO
from datetime import datetime
import textwrap

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black

# =============================
# Streamlit-app (ingen Flask)
# =============================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

# ---------- Design (äggskalsvit bakgrund) ----------
# Fast äggskalsvit (från din bild) – ändra hex om du vill finjustera
eggshell_hex = "#F8F1E7"

# Applicera bakgrund i UI
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {eggshell_hex}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      /* Typografi – matcha PDF (Helvetica) */
      html, body, [class*="css"] { font-family: Helvetica, Arial, sans-serif; }
      /* H1 = 22pt ≈ 29px */
      .stMarkdown h1 { font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }
      /* H2 = 14pt ≈ 18.7px */
      .stMarkdown h2 { font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }
      /* Brödtext = 11pt ≈ 14.7px, radavstånd ≈ 16pt → ~21px */
      .stMarkdown p, .stMarkdown { font-size: 15px; line-height: 21px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Datamodell för sidans innehåll ----------
# Allt innehåll renderas från denna modell OCH samma modell används för PDF.
PAGE_TITLE_LINES = ["Självskattning", "Funktionellt ledarskap"]  # två rader, samma storlek
SECTIONS = [
    {
        "title": "Aktivt lyssnande",
        "text": (
            "Förmågan att vara närvarande i samtal och aktivt lyssna på medarbetare är en grundläggande del av ett "
            "funktionellt ledarskap. Det handlar om att verkligen förstå vad den andra personen säger – både genom ord "
            "och känslor – och visa att du lyssnar. Reflektera över hur ofta du skapar utrymme för andra att uttrycka "
            "sig utan att avbryta."
        ),
    },
    {
        "title": "Återkoppling",
        "text": (
            "Återkoppling är en central del i ledarskap som skapar utveckling, tydlighet och motivation. Fundera på hur "
            "du ger återkoppling – både positiv och korrigerande – och om den landar på ett sätt som stärker förtroendet. "
            "Ett funktionellt ledarskap bygger på kontinuerlig, konstruktiv återkoppling."
        ),
    },
    {
        "title": "Målinriktning",
        "text": (
            "Att vara målinriktad handlar inte bara om att sätta upp mål, utan att skapa mening och riktning i vardagen. "
            "Hur tydliga är era mål i teamet? Vet alla varför de gör det de gör? Reflektera över hur du som ledare skapar "
            "engagemang kring målen."
        ),
    },
]

# ---------- Rendera sidan ----------
# Två H1-rubriker för samma teckenstorlek
st.markdown(f"# {PAGE_TITLE_LINES[0]}")
st.markdown(f"# {PAGE_TITLE_LINES[1]}")

for block in SECTIONS:
    st.header(block["title"])  # H2
    st.write(block["text"])    # brödtext

st.divider()
st.caption("Klicka på knappen nedan för att ladda ner en PDF som speglar allt innehåll på sidan.")

# ---------- PDF-generering från samma datamodell ----------

def generate_pdf_from_sections(title_lines, sections):
    """Skapar en PDF som speglar sidans design: två H1-rader, äggskalsvit bakgrund, rubriker & brödtext."""
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Bakgrund (äggskalsvit)
    pdf.setFillColor(HexColor(eggshell_hex))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(black)  # tillbaka till svart text

    # Marginaler och typografi
    margin_x = 50
    top_y = height - 60
    h1_size = 22  # samma storlek för båda rader
    h2_size = 14
    body_size = 11
    line_h = 16  # radavstånd för brödtext

    # Dokumenttitel
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    # Rita två H1-rader med samma storlek
    current_y = top_y
    pdf.setFont("Helvetica-Bold", h1_size)
    for line in title_lines:
        if line.strip():
            pdf.drawString(margin_x, current_y, line)
            current_y -= h1_size + 4  # spacing mellan titelrader

    # Tidsstämpel övre högra hörnet
    pdf.setFont("Helvetica", 9)
    timestamp = datetime.now().strftime("Genererad: %Y-%m-%d %H:%M")
    pdf.drawRightString(width - margin_x, top_y + 4, timestamp)

    # Startposition för textflöde
    y = current_y - 10

    def ensure_space(needed_px: int):
        nonlocal y
        if y - needed_px < 50:  # sidfotmarginal
            pdf.showPage()
            # Ny sida med samma bakgrund & liten sidhuvudstitel
            pdf.setFillColor(HexColor(eggshell_hex))
            pdf.rect(0, 0, width, height, fill=1, stroke=0)
            pdf.setFillColor(black)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin_x, height - 40, " ".join(title_lines))
            y = height - 60

    for block in sections:
        # Sektionstitel (H2)
        ensure_space(30)
        pdf.setFont("Helvetica-Bold", h2_size)
        pdf.drawString(margin_x, y, block["title"])
        y -= h2_size + 6

        # Brödtext
        pdf.setFont("Helvetica", body_size)
        wrapped = textwrap.wrap(block["text"], width=95)
        for line in wrapped:
            ensure_space(line_h)
            pdf.drawString(margin_x, y, line)
            y -= line_h
        y -= 6  # extra luft mellan sektioner

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()


pdf_bytes = generate_pdf_from_sections(PAGE_TITLE_LINES, SECTIONS)

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
    type="primary",
)
