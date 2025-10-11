from io import BytesIO
from datetime import datetime
import textwrap

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# Streamlit-app (ingen Flask)
# =============================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

# ---------- Design (äggskalsvit bakgrund & typografi) ----------
eggshell_hex = "#FAF7F0"  # fast äggskalsvit enligt önskemål
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {eggshell_hex}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      /* Typografi – matcha PDF (Helvetica) */
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
      /* H1 = 22pt ≈ 29px */
      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      /* H2 = 14pt ≈ 19px */
      .stMarkdown h2 {{ font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }}
      /* Brödtext = 11pt ≈ 15px, radavstånd ≈ 21px */
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}
      /* Resultat-kort (likt bilden) */
      .card {{ background: #fff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.08); padding: 14px 16px; border: 1px solid rgba(0,0,0,.12); }}
      .card h3 {{ margin: 0 0 8px 0; font-size: 16px; }}
      .score {{ font-size: 40px; font-weight: 800; margin: 4px 0 8px 0; }}
      .summa {{ font-size: 13px; color: #333; margin-top: 8px; }}
      .barbg {{ width: 100%; height: 10px; background: #E9ECEF; border-radius: 6px; overflow: hidden; }}
      .barfill {{ height: 10px; background: #F5A524; display: block; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Datamodell ----------
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"
SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "text": (
            "I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och "
            "lösningarna på verksamhetens utmaningar.\n\n"
            "Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som "
            "sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog "
            "och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.\n\n"
            "Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både "
            "engagemang, förtroende och delaktighet."
        ),
        "max": 56,
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "text": (
            "Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som "
            "förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och "
            "förväntade beteenden skapar du trygghet och fokus i arbetet.\n\n"
            "Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv "
            "feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du "
            "önskvärda beteenden och hjälper dina medarbetare att lyckas.\n\n"
            "I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser "
            "visar ledarskap på riktigt."
        ),
        "max": 56,
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "text": (
            "Målinriktat ledarskap handlar om att ge tydliga ramar – tid, resurser och ansvar – så att medarbetare kan "
            "arbeta effektivt och med trygghet. Tydliga och inspirerande mål skapar riktning och hjälper alla att "
            "förstå vad som är viktigt just nu.\n\n"
            "Som chef handlar det om att formulera mål som går att tro på, och att tydliggöra hur de ska nås. När du "
            "delegerar ansvar och befogenheter visar du förtroende och skapar engagemang. Målen blir då inte bara "
            "något att leverera på – utan något att vara delaktig i.\n\n"
            "Uppföljning är nyckeln. Genom att uppmärksamma framsteg, ge återkoppling och fira resultat förstärker du "
            "både prestation och motivation."
        ),
        "max": 35,
    },
]

# ---------- Rendera titel ----------
st.markdown(f"# {PAGE_TITLE}")

# ---------- Sektioner 68%/32% + resultatkort ----------
results = {}
for block in SECTIONS:
    left, right = st.columns([0.68, 0.32])  # 68% / 32%
    with left:
        st.header(block["title"])  # H2
        for para in block["text"].split("\n\n"):
            st.write(para)
    with right:
        score = st.number_input(
            f"Ange resultat – {block['title']}",
            min_value=0,
            max_value=block["max"],
            value=0,
            step=1,
            key=f"score_{block['key']}",
            help=f"Sätt värdet för denna del (0–{block['max']}).",
        )
        results[block["key"]] = int(score)
        # Resultat-kort likt bilden
        st.markdown(
            f"""
            <div class=\"card\">
              <h3>{block['title']}</h3>
              <div class=\"score\">{score}</div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(score / block["max"] if block["max"] else 0.0)
        st.markdown(
            f"""
              <div class=\"barbg\"><span class=\"barfill\" style=\"width:{(score/block['max']*100) if block['max'] else 0:.0f}%\"></span></div>
              <div class=\"summa\">Summa {score}/{block['max']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()
st.caption("Klicka på knappen nedan för att ladda ner en PDF som speglar allt innehåll – texter och resultat.")

# ---------- PDF-generering från samma datamodell ----------

def generate_pdf(title: str, sections, results_map):
    """Skapar en PDF som speglar sidans design och inkluderar resultatruta per sektion."""
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Bakgrund (äggskalsvit)
    pdf.setFillColor(HexColor(eggshell_hex))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(black)

    # Marginaler och typografi
    margin_x = 50
    top_y = height - 60
    h1_size = 22
    h2_size = 14
    body_size = 11
    line_h = 16

    # Dokumenttitel
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    # H1 (en rad)
    pdf.setFont("Helvetica-Bold", h1_size)
    pdf.drawString(margin_x, top_y, title)

    # Tidsstämpel
    pdf.setFont("Helvetica", 9)
    timestamp = datetime.now().strftime("Genererad: %Y-%m-%d %H:%M")
    pdf.drawRightString(width - margin_x, top_y + 4, timestamp)

    # Startposition
    y = top_y - 28

    def ensure_space(needed_px: int):
        nonlocal y
        if y - needed_px < 50:
            pdf.showPage()
            pdf.setFillColor(HexColor(eggshell_hex))
            pdf.rect(0, 0, width, height, fill=1, stroke=0)
            pdf.setFillColor(black)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin_x, height - 40, title)
            y = height - 60

    # Färger för progressbar i PDF
    bar_bg = Color(0.91, 0.92, 0.94)  # ljusgrå bakgrund
    bar_fg = Color(0.96, 0.65, 0.15)  # orange fyllnad

    for block in sections:
        ensure_space(30)
        pdf.setFont("Helvetica-Bold", h2_size)
        pdf.drawString(margin_x, y, block["title"])
        y -= h2_size + 6

        # Brödtext
        pdf.setFont("Helvetica", body_size)
        wrapped = []
        for para in block["text"].split("\n\n"):
            wrapped += textwrap.wrap(para, width=95) + [""]
        for line in wrapped:
            ensure_space(line_h)
            if line:
                pdf.drawString(margin_x, y, line)
            y -= line_h

        # Resultat-rad (etikett + stapel)
        score_val = int(results_map.get(block["key"], 0))
        max_val = int(block.get("max", 0))
        ensure_space(36)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin_x, y, f"Summa {score_val}/{max_val}")
        y -= 12
        bar_w = width - margin_x * 2
        bar_h = 8
        pdf.setFillColor(bar_bg)
        pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = 0 if max_val == 0 else bar_w * (score_val / max_val)
        pdf.setFillColor(bar_fg)
        pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
        pdf.setFillColor(black)
        y -= 18

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()


pdf_bytes = generate_pdf(PAGE_TITLE, SECTIONS, results)

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
    type="primary",
)
