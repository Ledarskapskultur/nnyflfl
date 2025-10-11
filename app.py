import textwrap
from io import BytesIO
from datetime import datetime

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# =============================
# Streamlit-app (ingen Flask)
# =============================
st.set_page_config(
    page_title="Självskattning - Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

st.title("Självskattning - Funktionellt ledarskap")

st.header("Aktivt lyssnande")
st.write(
    """
    Förmågan att vara närvarande i samtal och aktivt lyssna på medarbetare är en grundläggande del av ett funktionellt ledarskap.
    Det handlar om att verkligen förstå vad den andra personen säger – både genom ord och känslor – och visa att du lyssnar.
    Reflektera över hur ofta du skapar utrymme för andra att uttrycka sig utan att avbryta.
    """
)

st.header("Återkoppling")
st.write(
    """
    Återkoppling är en central del i ledarskap som skapar utveckling, tydlighet och motivation.
    Fundera på hur du ger återkoppling – både positiv och korrigerande – och om den landar på ett sätt som stärker förtroendet.
    Ett funktionellt ledarskap bygger på kontinuerlig, konstruktiv återkoppling.
    """
)

st.header("Målinriktning")
st.write(
    """
    Att vara målinriktad handlar inte bara om att sätta upp mål, utan att skapa mening och riktning i vardagen.
    Hur tydliga är era mål i teamet? Vet alla varför de gör det de gör? Reflektera över hur du som ledare skapar engagemang kring målen.
    """
)


def generate_pdf() -> bytes:
    """Genererar en PDF av innehållet ovan och returnerar som bytes."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    width, height = A4
    margin = 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, height - margin, "Självskattning - Funktionellt ledarskap")

    pdf.setFont("Helvetica", 10)
    datum = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.drawString(margin, height - margin - 20, f"Genererad: {datum}")

    # Skriv textblocken
    textobject = pdf.beginText()
    textobject.setTextOrigin(margin, height - margin - 60)
    textobject.setFont("Helvetica", 12)

    innehall = (
        "Aktivt lyssnande:\n"
        "Förmågan att vara närvarande i samtal och aktivt lyssna på medarbetare är en grundläggande del av ett funktionellt ledarskap.\n\n"
        "Återkoppling:\n"
        "Återkoppling är en central del i ledarskap som skapar utveckling, tydlighet och motivation.\n\n"
        "Målinriktning:\n"
        "Att vara målinriktad handlar inte bara om att sätta upp mål, utan att skapa mening och riktning i vardagen.\n"
    )

    import textwrap as tw
    for line in tw.wrap(innehall, width=90):
        textobject.textLine(line)

    pdf.drawText(textobject)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()

# Generera PDF och visa nedladdningsknapp
pdf_bytes = generate_pdf()

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
)

st.caption("Klicka på knappen ovan för att ladda ner en PDF av innehållet.")
