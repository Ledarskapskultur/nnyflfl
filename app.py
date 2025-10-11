from io import BytesIO
from datetime import datetime
import textwrap

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# =============================
# Streamlit-app (ingen Flask)
# =============================
st.set_page_config(
    page_title="Självskattning Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

# ---------- Datamodell för sidans innehåll ----------
# Allt som visas på sidan hämtas från denna struktur.
# PDF:en genereras från exakt samma data → hålls i synk.
PAGE_TITLE = "Självskattning <br> Funktionellt ledarskap"
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
st.title(PAGE_TITLE)
for block in SECTIONS:
    st.header(block["title"])
    st.write(block["text"])

st.divider()
st.caption("Klicka på knappen nedan för att ladda ner en PDF som speglar allt innehåll på sidan.")

# ---------- PDF-generering från samma datamodell ----------

def generate_pdf_from_sections(page_title: str, sections: list[dict]) -> bytes:
    """Skapar en PDF som speglar allt innehåll på sidan.
    Hanterar radbrytningar och sidbrytningar för längre texter.
    """
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Marginaler och typografi
    margin_x = 50
    top_y = height - 50
    line_h = 16  # radavstånd för brödtext

    # Sidhuvud
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin_x, top_y, page_title)

    pdf.setFont("Helvetica", 9)
    timestamp = datetime.now().strftime("Genererad: %Y-%m-%d %H:%M")
    pdf.drawRightString(width - margin_x, top_y, timestamp)

    # Startposition för textflöde
    y = top_y - 30

    def ensure_space(needed_px: int):
        nonlocal y
        if y - needed_px < 40:  # sidfotmarginal
            pdf.showPage()
            # Ny sida, skriv rubrik i sidhuvud litet
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin_x, height - 40, page_title)
            y = height - 60

    for block in sections:
        # Rubrik för sektion
        ensure_space(30)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(margin_x, y, block["title"])
        y -= 20

        # Brödtext med ord-brytning
        pdf.setFont("Helvetica", 12)
        wrapped = textwrap.wrap(block["text"], width=95)
        for line in wrapped:
            ensure_space(line_h)
            pdf.drawString(margin_x, y, line)
            y -= line_h

        # Avstånd mellan sektioner
        y -= 10

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()


pdf_bytes = generate_pdf_from_sections(PAGE_TITLE, SECTIONS)

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
    type="primary",
)
