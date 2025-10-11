from io import BytesIO
from datetime import datetime
import textwrap

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# Grundinställningar (Streamlit)
# =============================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

EGGSHELL = "#FAF7F0"

# Global CSS
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {EGGSHELL}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      .stMarkdown h2 {{ font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }}
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}

      /* Kort/komponenter */
      .card {{ background:#fff; border-radius:14px; border:1px solid rgba(0,0,0,.10);
               box-shadow:0 6px 20px rgba(0,0,0,.08); }}
      .hero {{ text-align:center; padding:34px 28px; }}
      .hero h1 {{ font-size:34px; margin:0 0 8px 0; }}
      .hero p  {{ color:#374151; margin:0 0 18px 0; }}

      /* Kontakt */
      .contact-card {{ padding:12px 14px; }}
      .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}
      .stTextInput>div>div>input {{ background:#F8FAFC; }}

      /* Resultatkort (bedömning) */
      .right-wrap {{ display:flex; align-items:center; justify-content:center; }}
      .res-card {{ max-width:360px; width:100%; padding:16px 18px; }}
      .role-label {{ font-size:13px; color:#111827; margin:10px 0 6px 0; display:block; font-weight:600; }}
      .barbg {{ width:100%; height:10px; background:#E9ECEF; border-radius:6px; overflow:hidden; }}
      .barfill {{ height:10px; display:block; }}
      .bar-green {{ background:#4CAF50; }}
      .bar-orange {{ background:#F5A524; }}
      .bar-blue {{ background:#3B82F6; }}
      .maxline {{ font-size:13px; color:#374151; margin-top:12px; font-weight:600; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Data
# =============================
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "text": """I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och lösningarna på verksamhetens utmaningar.

Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.

Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både engagemang, förtroende och delaktighet.""",
        "max": 49,
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "text": """Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och förväntade beteenden skapar du trygghet och fokus i arbetet.

Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du önskvärda beteenden och hjälper dina medarbetare att lyckas.

I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser visar ledarskap på riktigt.""",
        "max": 56,
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "text": """Målinriktat ledarskap handlar om att ge tydliga ramar – tid, resurser och ansvar – så att medarbetare kan arbeta effektivt och med trygghet. Tydliga och inspirerande mål skapar riktning och hjälper alla att förstå vad som är viktigt just nu.

Som chef handlar det om att formulera mål som går att tro på, och att tydliggöra hur de ska nås. När du delegerar ansvar och befogenheter visar du förtroende och skapar engagemang. Målen blir då inte bara något att leverera på – utan något att vara delaktig i.

Uppföljning är nyckeln. Genom att uppmärksamma framsteg, ge återkoppling och fira resultat förstärker du både prestation och motivation.""",
        "max": 35,
    },
]

# Poäng per roll (visas – ingen inmatning)
preset_scores = {
    "lyssnande":   {"chef": 0, "overchef": 0, "medarbetare": 0},
    "aterkoppling":{"chef": 0, "overchef": 0, "medarbetare": 0},
    "malinriktning":{"chef": 0, "overchef": 0, "medarbetare": 0},
}

ROLE_LABELS = {"chef": "Chef", "overchef": "Överordnad chef", "medarbetare": "Medarbetare"}
ROLE_ORDER  = ["chef", "overchef", "medarbetare"]
ROLES_REQUIRE_CODE = {"Överordnad chef", "Medarbetare"}  # roller som kräver Kod

# =============================
# LANDNINGSSIDA
# =============================
def render_landing():
    st.markdown(
        """
        <div class="card hero">
          <h1>Självskattning – Funktionellt ledarskap</h1>
          <p>Fyll i dina uppgifter nedan och starta självskattningen.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Förifyll om användaren redan varit här
    default = st.session_state.get(
        "kontakt",
        {"Namn": "", "Företag": "", "Telefon": "", "E-post": "", "Funktion": "Chef", "Kod": ""},
    )

    with st.form("landing_form"):
        # 3 kolumner så att Kod hamnar till höger om Funktion
        c1, c2, c3 = st.columns([0.34, 0.33, 0.33])
        with c1:
            namn     = st.text_input("Namn", value=default["Namn"])
            telefon  = st.text_input("Telefon", value=default["Telefon"])
        with c2:
            foretag  = st.text_input("Företag", value=default["Företag"])
            epost    = st.text_input("E-post", value=default["E-post"])
        with c3:
            funktion = st.selectbox(
                "Funktion", ["Chef", "Överordnad chef", "Medarbetare"],
                index=["Chef", "Överordnad chef", "Medarbetare"].index(default["Funktion"])
            )
            # Visa kodfält om rollen kräver kod, annars visa ett "disabled" fält som är grått
            visa_kod = funktion in ROLES_REQUIRE_CODE
            kod = st.text_input("Kod (obligatorisk)", value=default["Kod"], disabled=not visa_kod)

        start = st.form_submit_button("Starta självskattning", type="primary")

    if start:
        # Validering
        if not namn.strip() or not epost.strip():
            st.warning("Fyll i minst Namn och E-post för att fortsätta.")
            return
        if funktion in ROLES_REQUIRE_CODE and not kod.strip():
            st.warning("Kod är obligatoriskt för vald funktion.")
            return

        st.session_state["kontakt"] = {
            "Namn": namn.strip(),
            "Företag": foretag.strip(),
            "Telefon": telefon.strip(),
            "E-post": epost.strip(),
            "Funktion": funktion,
            "Kod": kod.strip() if funktion in ROLES_REQUIRE_CODE else "",
        }
        st.session_state["page"] = "assessment"

# =============================
# BEDÖMNINGS-SIDA
# =============================
def render_assessment():
    st.markdown(f"# {PAGE_TITLE}")

    # Kontaktuppgifter (förifyll från landing)
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card contact-card'>", unsafe_allow_html=True)

        base = st.session_state.get("kontakt", {"Namn":"","Företag":"","Telefon":"","E-post":"","Funktion":"Chef","Kod":""})

        # 3 kolumner: Namn/E-post | Företag/Telefon | Funktion/Kod
        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
        with c1:
            kontakt_namn  = st.text_input("Namn", value=base.get("Namn",""))
            kontakt_epost = st.text_input("E-post", value=base.get("E-post",""))
        with c2:
            kontakt_foretag = st.text_input("Företag", value=base.get("Företag",""))
            kontakt_tel     = st.text_input("Telefon", value=base.get("Telefon",""))
        with c3:
            kontakt_funktion = st.selectbox(
                "Funktion", ["Chef", "Överordnad chef", "Medarbetare"],
                index=["Chef", "Överordnad chef", "Medarbetare"].index(base.get("Funktion","Chef"))
            )
            visa_kod = kontakt_funktion in ROLES_REQUIRE_CODE
            kontakt_kod = st.text_input("Kod (obligatorisk)", value=base.get("Kod",""), disabled=not visa_kod)

        # spara ev. ändringar
        st.session_state["kontakt"] = {
            "Namn": kontakt_namn.strip(),
            "Företag": kontakt_foretag.strip(),
            "Telefon": kontakt_tel.strip(),
            "E-post": kontakt_epost.strip(),
            "Funktion": kontakt_funktion,
            "Kod": kontakt_kod.strip() if visa_kod else "",
        }
        st.markdown("</div>", unsafe_allow_html=True)

    kontakt = st.session_state["kontakt"]

    # Sektioner 68/32 + resultatkort i önskat format
    for block in SECTIONS:
        left, right = st.columns([0.68, 0.32])
        with left:
            st.header(block["title"])
            for para in block["text"].split("\n\n"):
                st.write(para)
        with right:
            scores = preset_scores.get(block["key"], {"chef":0,"overchef":0,"medarbetare":0})

            st.markdown("<div class='right-wrap'>", unsafe_allow_html=True)
            html = [f"<div class='card res-card'>"]

            # Chef
            val = int(scores.get("chef", 0)); pct = 0 if block["max"]==0 else val/block["max"]*100
            html += [f"<span class='role-label'>Chef: {val} poäng</span>",
                     f"<div class='barbg'><span class='barfill bar-green' style='width:{pct:.0f}%'></span></div>"]

            # Överordnad chef
            val = int(scores.get("overchef", 0)); pct = 0 if block["max"]==0 else val/block["max"]*100
            html += [f"<span class='role-label'>Överordnad chef: {val} poäng</span>",
                     f"<div class='barbg'><span class='barfill bar-orange' style='width:{pct:.0f}%'></span></div>"]

            # Medarbetare
            val = int(scores.get("medarbetare", 0)); pct = 0 if block["max"]==0 else val/block["max"]*100
            html += [f"<span class='role-label'>Medarbetare: {val} poäng</span>",
                     f"<div class='barbg'><span class='barfill bar-blue' style='width:{pct:.0f}%'></span></div>"]

            # Max
            html += [f"<div class='maxline'>Max: {block['max']} poäng</div>", "</div>"]
            st.markdown("\n".join(html), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Disable PDF-knapp om kod krävs men saknas
    disable_pdf = (kontakt["Funktion"] in ROLES_REQUIRE_CODE) and (not kontakt["Kod"])
    if disable_pdf:
        st.warning("Kod är obligatoriskt för vald funktion.")
    st.caption("Ladda ner en PDF som speglar allt innehåll – kontakt, texter och resultat.")

    # ----- PDF (matchar UI-format) -----
    def generate_pdf(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
        buf = BytesIO()
        pdf = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,width,height,fill=1,stroke=0)
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
            f"Namn: {kontaktinfo.get('Namn','')}",
            f"Företag: {kontaktinfo.get('Företag','')}",
            f"Telefon: {kontaktinfo.get('Telefon','')}",
            f"E-post: {kontaktinfo.get('E-post','')}",
            f"Funktion: {kontaktinfo.get('Funktion','')}",
        ]
        if kontaktinfo.get("Funktion") in ROLES_REQUIRE_CODE:
            row.append(f"Kod: {kontaktinfo.get('Kod','')}")
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
                pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,width,height,fill=1,stroke=0)
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
            for p in block["text"].split("\n\n"):
                for ln in textwrap.wrap(p, width=95):
                    ensure_space(line_h); pdf.drawString(margin_x, y, ln); y -= line_h

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
        "Ladda ner PDF",
        data=pdf_bytes,
        file_name="självskattning_funktionellt_ledarskap.pdf",
        mime="application/pdf",
        type="primary",
        disabled=disable_pdf,
    )

    if st.button("◀ Tillbaka till startsidan"):
        st.session_state["page"] = "landing"

# =============================
# Enkel router
# =============================
if "page" not in st.session_state:
    st.session_state["page"] = "landing"

if st.session_state["page"] == "landing":
    render_landing()
else:
    render_assessment()
