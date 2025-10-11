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

# ---------- Design ----------
eggshell_hex = "#FAF7F0"
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {eggshell_hex}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      .stMarkdown h2 {{ font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }}
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}
      /* Resultat-kort */
      .card {{ background:#fff; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,.08);
               padding:14px 16px; border:1px solid rgba(0,0,0,.12); max-width:340px; margin:0 auto; }}
      .role-label {{ font-size:13px; color:#111827; margin:8px 0 4px 0; display:block; font-weight:600; }}
      .barbg {{ width:100%; height:10px; background:#E9ECEF; border-radius:6px; overflow:hidden; }}
      .barfill {{ height:10px; display:block; }}
      .bar-green {{ background:#4CAF50; }}
      .bar-orange {{ background:#F5A524; }}
      .bar-blue {{ background:#3B82F6; }}
      .maxline {{ font-size:13px; color:#374151; margin-top:10px; font-weight:600; }}
      .right-wrap {{ display:flex; align-items:center; justify-content:center; }}
      /* Kontaktuppgifter */
      .contact-card {{ background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:12px; padding:12px 14px;
                       box-shadow:0 4px 16px rgba(0,0,0,.06); }}
      .contact-title {{ font-weight:700; font-size:19px; margin:6px 0 10px 0; }}
      .stTextInput>div>div>input {{ background:#F8FAFC; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"
SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "text": """I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och lösningarna på verksamhetens utmaningar.

Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.

Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både engagemang, förtroende och delaktighet.""",
        "max": 49,  # 7 frågor
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "text": """Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och förväntade beteenden skapar du trygghet och fokus i arbetet.

Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du önskvärda beteenden och hjälper dina medarbetare att lyckas.

I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser visar ledarskap på riktigt.""",
        "max": 56,  # 8 frågor
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "text": """Målinriktat ledarskap handlar om att ge tydliga ramar – tid, resurser och ansvar – så att medarbetare kan arbeta effektivt och med trygghet. Tydliga och inspirerande mål skapar riktning och hjälper alla att förstå vad som är viktigt just nu.

Som chef handlar det om att formulera mål som går att tro på, och att tydliggöra hur de ska nås. När du delegerar ansvar och befogenheter visar du förtroende och skapar engagemang. Målen blir då inte bara något att leverera på – utan något att vara delaktig i.

Uppföljning är nyckeln. Genom att uppmärksamma framsteg, ge återkoppling och fira resultat förstärker du både prestation och motivation.""",
        "max": 35,  # 5 frågor
    },
]

# Sätt värden här (poäng per roll i varje del)
preset_scores = {
    "lyssnande":   {"chef": 0, "overchef": 0, "medarbetare": 0},
    "aterkoppling":{"chef": 0, "overchef": 0, "medarbetare": 0},
    "malinriktning":{"chef": 0, "overchef": 0, "medarbetare": 0},
}

ROLE_LABELS = {"chef": "Chef", "overchef": "Överordnad chef", "medarbetare": "Medarbetare"}
ROLE_ORDER  = ["chef", "overchef", "medarbetare"]

# ---------- Header ----------
st.markdown(f"# {PAGE_TITLE}")

# ---------- Kontaktuppgifter ----------
st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
with st.container():
    st.markdown("<div class='contact-card'>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([0.15, 0.2, 0.2, 0.2, 0.25])
    with c1: kontakt_id      = st.text_input("Unikt id", value="")
    with c2: kontakt_namn    = st.text_input("Namn", value="")
    with c3: kontakt_foretag = st.text_input("Företag", value="")
    with c4: kontakt_tel     = st.text_input("Telefon", value="")
    with c5: kontakt_epost   = st.text_input("E-post", value="")
    st.markdown("</div>", unsafe_allow_html=True)

kontakt = {
    "Unikt id": kontakt_id,
    "Namn": kontakt_namn,
    "Företag": kontakt_foretag,
    "Telefon": kontakt_tel,
    "E-post": kontakt_epost,
}

# ---------- Sektioner 68/32 + kort i önskat format ----------
for block in SECTIONS:
    left, right = st.columns([0.68, 0.32])
    with left:
        st.header(block["title"])
        for para in block["text"].split("\n\n"):
            st.write(para)
    with right:
        scores = preset_scores.get(block["key"], {r: 0 for r in ROLE_ORDER})

        st.markdown("<div class='right-wrap'>", unsafe_allow_html=True)
        html = [f"<div class='card'>"]
        # Chef
        val = int(scores.get("chef", 0)); pct = 0 if block["max"] == 0 else val/block["max"]*100
        html += [f"<span class='role-label'>Chef: {val} poäng</span>",
                 f"<div class='barbg'><span class='barfill bar-green' style='width:{pct:.0f}%'></span></div>"]
        # Överordnad chef
        val = int(scores.get("overchef", 0)); pct = 0 if block["max"] == 0 else val/block["max"]*100
        html += [f"<span class='role-label'>Överordnad chef: {val} poäng</span>",
                 f"<div class='barbg'><span class='barfill bar-orange' style='width:{pct:.0f}%'></span></div>"]
        # Medarbetare
        val = int(scores.get("medarbetare", 0)); pct = 0 if block["max"] == 0 else val/block["max"]*100
        html += [f"<span class='role-label'>Medarbetare: {val} poäng</span>",
                 f"<div class='barbg'><span class='barfill bar-blue' style='width:{pct:.0f}%'></span></div>"]
        # Max
        html += [f"<div class='maxline'>Max: {block['max']} poäng</div>", "</div>"]
        st.markdown("\n".join(html), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Klicka på knappen nedan för att ladda ner en PDF som speglar allt innehåll – kontakt, texter och resultat.")

# ---------- PDF: samma format ----------
def generate_pdf(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    pdf.setFillColor(HexColor(eggshell_hex)); pdf.rect(0,0,width,height,fill=1,stroke=0)
    pdf.setFillColor(black)

    margin_x = 50
    top_y = height - 60
    h1, h2, body, line_h = 22, 14, 11, 16

    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")
    pdf.setFont("Helvetica-Bold", h1); pdf.drawString(margin_x, top_y, title)
    pdf.setFont("Helvetica", 9); pdf.drawRightString(width-margin_x, top_y+4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
    y = top_y - 28

    # Kontakt
    pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    row = [
        f"Unikt id: {kontaktinfo.get('Unikt id','')}",
        f"Namn: {kontaktinfo.get('Namn','')}",
        f"Företag: {kontaktinfo.get('Företag','')}",
        f"Telefon: {kontaktinfo.get('Telefon','')}",
        f"E-post: {kontaktinfo.get('E-post','')}",
    ]
    line = "   |   ".join(row)
    if len(line) > 110:
        mid = len(row)//2
        pdf.drawString(margin_x, y, "   |   ".join(row[:mid])); y -= 14
        pdf.drawString(margin_x, y, "   |   ".join(row[mid:])); y -= 8
    else:
        pdf.drawString(margin_x, y, line); y -= 14

    def ensure_space(need:int):
        nonlocal y
        if y - need < 50:
            pdf.showPage()
            pdf.setFillColor(HexColor(eggshell_hex)); pdf.rect(0,0,width,height,fill=1,stroke=0)
            pdf.setFillColor(black); pdf.setFont("Helvetica",9)
            pdf.drawString(margin_x, height-40, title)
            y = height - 60

    bar_bg = Color(0.91,0.92,0.94)
    bar_green  = Color(0.30,0.69,0.31)
    bar_orange = Color(0.96,0.65,0.15)
    bar_blue   = Color(0.23,0.51,0.96)

    for block in sections:
        ensure_space(30)
        pdf.setFont("Helvetica-Bold", h2); pdf.drawString(margin_x, y, block["title"]); y -= h2 + 6

        pdf.setFont("Helvetica", body)
        wrapped=[]
        for p in block["text"].split("\n\n"):
            wrapped += textwrap.wrap(p, width=95) + [""]
        for ln in wrapped:
            ensure_space(line_h)
            if ln: pdf.drawString(margin_x, y, ln)
            y -= line_h

        # Chef
        chef = int(results_map.get(block["key"], {}).get("chef", 0))
        ensure_space(26)
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"Chef: {chef} poäng"); y -= 12
        bar_w, bar_h = width-2*margin_x, 8
        pdf.setFillColor(bar_bg); pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = 0 if block["max"]==0 else bar_w*(chef/block["max"])
        pdf.setFillColor(bar_green); pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
        pdf.setFillColor(black); y -= 14

        # Överordnad chef
        oc = int(results_map.get(block["key"], {}).get("overchef", 0))
        ensure_space(26)
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"Överordnad chef: {oc} poäng"); y -= 12
        pdf.setFillColor(bar_bg); pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = 0 if block["max"]==0 else bar_w*(oc/block["max"])
        pdf.setFillColor(bar_orange); pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
        pdf.setFillColor(black); y -= 14

        # Medarbetare
        med = int(results_map.get(block["key"], {}).get("medarbetare", 0))
        ensure_space(26)
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"Medarbetare: {med} poäng"); y -= 12
        pdf.setFillColor(bar_bg); pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = 0 if block["max"]==0 else bar_w*(med/block["max"])
        pdf.setFillColor(bar_blue); pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
        pdf.setFillColor(black); y -= 16

        # Max
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"Max: {block['max']} poäng")
        y -= 18

    pdf.showPage(); pdf.save(); buf.seek(0)
    return buf.getvalue()

pdf_bytes = generate_pdf(PAGE_TITLE, SECTIONS, preset_scores, kontakt)

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
    type="primary",
)
