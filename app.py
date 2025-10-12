from io import BytesIO
from datetime import datetime
import os
import json
import secrets
import string
import textwrap
import requests

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# App setup & theme
# =============================
st.set_page_config(page_title="Självskattning – Funktionellt ledarskap", page_icon="📄", layout="centered")
EGGSHELL = "#FAF7F0"
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {EGGSHELL}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      .stMarkdown h2 {{ font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }}
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}
      .card {{ background:#fff; border-radius:12px; border:1px solid rgba(0,0,0,.12);
               box-shadow:0 6px 20px rgba(0,0,0,.08); padding:14px 16px; }}
      .hero {{ text-align:center; padding:34px 28px; }}
      .hero h1 {{ font-size:34px; margin:0 0 8px 0; }}
      .hero p  {{ color:#374151; margin:0 0 18px 0; }}
      .contact-card {{ padding:12px 14px; }}
      .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}
      .right-wrap {{ display:flex; align-items:center; justify-content:center; }}
      .res-card {{ max-width:380px; width:100%; padding:16px 18px; }}
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

# Poäng per roll (sätt här)
preset_scores = {
    "lyssnande":   {"chef": 0, "overchef": 0, "medarbetare": 0},
    "aterkoppling":{"chef": 0, "overchef": 0, "medarbetare": 0},
    "malinriktning":{"chef": 0, "overchef": 0, "medarbetare": 0},
}

ROLES_REQUIRE_ID = {"Överordnad chef", "Medarbetare"}

# =============================
# Power Automate webhook
# =============================
FLOW_URL_DEFAULT = "https://default1ad3791223f4412ea6272223201343.20.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/bff5923897b04a39bc6ba69ea4afde69/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=B1rjO0FhY0ZxXO8VJvWPmcLAv-LMCgICG6tDguPmhwQ"
FLOW_URL = os.getenv("FLOW_URL", FLOW_URL_DEFAULT).strip()

def send_to_flow(payload: dict) -> tuple[bool, str | None, str | None]:
    """POST to Power Automate. Returns (ok, returned_unikt_id, error)."""
    if not FLOW_URL:
        return False, None, "FLOW_URL saknas."
    try:
        r = requests.post(FLOW_URL, json=payload, timeout=25)
        if 200 <= r.status_code < 300:
            try:
                data = r.json() if r.content else {}
            except Exception:
                data = {}
            uid = (
                data.get("uniktId") or data.get("unikt_id") or data.get("id")
                or data.get("uniqueId") or data.get("UniqueId")
            )
            return True, (str(uid) if uid is not None else None), None
        return False, None, f"HTTP {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return False, None, str(e)

def generate_unikt_id(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

# =============================
# UI: Landing
# =============================
def render_landing():
    st.markdown(
        """
        <div class="card hero">
          <h1>Självskattning  Funktionellt ledarskap</h1>
          <p>Fyll i dina uppgifter nedan och starta självskattningen.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    default = st.session_state.get("kontakt", {"Namn":"", "Företag":"", "Telefon":"", "E-post":"", "Funktion":"Chef", "Unikt id":""})

    with st.form("landing_form"):
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            namn = st.text_input("Namn", value=default["Namn"])
            telefon = st.text_input("Telefon", value=default["Telefon"])
            funktion = st.selectbox("Funktion", ["Chef", "Överordnad chef", "Medarbetare"],
                                    index=["Chef","Överordnad chef","Medarbetare"].index(default["Funktion"]))
        with c2:
            foretag = st.text_input("Företag", value=default["Företag"])
            epost   = st.text_input("E-post", value=default["E-post"])
        start = st.form_submit_button("Starta", type="primary")

    if start:
        if not namn.strip() or not epost.strip():
            st.warning("Fyll i minst Namn och E-post för att fortsätta.")
            return

        # Generate a unique id immediately
        generated_id = generate_unikt_id()

        st.session_state["kontakt"] = {
            "Namn": namn.strip(),
            "Företag": foretag.strip(),
            "Telefon": telefon.strip(),
            "E-post": epost.strip(),
            "Funktion": funktion,
            "Unikt id": generated_id if funktion == "Chef" else "",
        }

        if funktion == "Chef":
            # Prepare sums for Flow schema (chef's scores)
            sum_listening = int(preset_scores.get("lyssnande", {}).get("chef", 0))
            sum_feedback  = int(preset_scores.get("aterkoppling", {}).get("chef", 0))
            sum_goal      = int(preset_scores.get("malinriktning", {}).get("chef", 0))
            answers = []  # keep for future use
            payload = {
                # REQUIRED (per your schema)
                "title": PAGE_TITLE,
                "name": namn.strip(),
                "company": foretag.strip(),          # optional in schema, we include it
                "email": epost.strip(),
                "sumListening": sum_listening,
                "sumFeedback":  sum_feedback,
                "sumGoal":      sum_goal,
                "answersJson":  json.dumps(answers, ensure_ascii=False),
                "submittedAt":  datetime.utcnow().isoformat() + "Z",
                "secret":       generated_id,       # <<< UNIQUE ID goes here
                "hasPdf":       False,
                "pdfBase64":    "",                 # empty (no PDF upload at start)
                "fileName":     "",                 # empty
            }
            ok, returned_uid, err = send_to_flow(payload)
            if ok:
                st.session_state["kontakt"]["Unikt id"] = returned_uid or generated_id
                st.success(f"Post skapad i SharePoint. Unikt id: {st.session_state['kontakt']['Unikt id']}", icon="✅")
                st.session_state["page"] = "assessment"
            else:
                st.error(f"Kunde inte skicka till Power Automate: {err}", icon="🚫")
        else:
            st.session_state["page"] = "id_page"  # Overordnad/Medarbetare enters id manually

# =============================
# UI: Enter ID page (for Överordnad/Medarbetare)
# =============================
def render_id_page():
    st.markdown("## Ange unikt id")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")
    base = st.session_state.get("kontakt", {})
    with st.form("id_form"):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            unikt_id = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write("")
            st.write(f"**Funktion:** {base.get('Funktion','')}")
        ok = st.form_submit_button("Fortsätt till självskattning", type="primary")
    if ok:
        if not unikt_id.strip():
            st.warning("Ange ett unikt id för att fortsätta.")
            return
        st.session_state["kontakt"]["Unikt id"] = unikt_id.strip()
        st.session_state["page"] = "assessment"
    if st.button("◀ Tillbaka"):
        st.session_state["page"] = "landing"

# =============================
# Assessment + PDF
# =============================
def render_assessment():
    st.markdown(f"# {PAGE_TITLE}")

    # Contact block
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card contact-card'>", unsafe_allow_html=True)
        base = st.session_state.get("kontakt", {"Namn":"","Företag":"","Telefon":"","E-post":"","Funktion":"Chef","Unikt id":""})
        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
        with c1:
            kontakt_namn  = st.text_input("Namn", value=base.get("Namn",""))
            kontakt_epost = st.text_input("E-post", value=base.get("E-post",""))
        with c2:
            kontakt_foretag = st.text_input("Företag", value=base.get("Företag",""))
            kontakt_tel     = st.text_input("Telefon", value=base.get("Telefon",""))
        with c3:
            kontakt_funktion = st.selectbox("Funktion", ["Chef", "Överordnad chef", "Medarbetare"],
                                            index=["Chef","Överordnad chef","Medarbetare"].index(base.get("Funktion","Chef")))
            kontakt_unikt_id = st.text_input("Unikt id", value=base.get("Unikt id",""), disabled=False)
        st.session_state["kontakt"] = {
            "Namn": kontakt_namn.strip(),
            "Företag": kontakt_foretag.strip(),
            "Telefon": kontakt_tel.strip(),
            "E-post": kontakt_epost.strip(),
            "Funktion": kontakt_funktion,
            "Unikt id": kontakt_unikt_id.strip(),
        }
        st.markdown("</div>", unsafe_allow_html=True)

    kontakt = st.session_state["kontakt"]

    # Sections 68/32 + 3 bars
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
            def bar(label, value, maxv, color_cls):
                pct = 0 if maxv == 0 else value/maxv*100
                return [
                    f"<span class='role-label'>{label}: {value} poäng</span>",
                    f"<div class='barbg'><span class='barfill {color_cls}' style='width:{pct:.0f}%'></span></div>",
                ]
            html += bar("Chef",            int(scores.get("chef",0)),        block["max"], "bar-green")
            html += bar("Överordnad chef", int(scores.get("overchef",0)),    block["max"], "bar-orange")
            html += bar("Medarbetare",     int(scores.get("medarbetare",0)), block["max"], "bar-blue")
            html += [f"<div class='maxline'>Max: {block['max']} poäng</div>", "</div>"]
            st.markdown("\n".join(html), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.caption("Ladda ner en PDF som speglar allt innehåll – kontakt, texter och resultat.")

    # PDF (same style)
    def generate_pdf(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
        buf = BytesIO()
        pdf = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,width,height,fill=1,stroke=0)
        pdf.setFillColor(black)
        margin_x = 50; top_y = height-60
        h1,h2,body,line_h = 22,14,11,16
        pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")
        pdf.setFont("Helvetica-Bold", h1); pdf.drawString(margin_x, top_y, title)
        pdf.setFont("Helvetica", 9); pdf.drawRightString(width-margin_x, top_y+4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
        y = top_y-28
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, "Kontaktuppgifter"); y -= 14
        pdf.setFont("Helvetica", 10)
        row = [
            f"Unikt id: {kontaktinfo.get('Unikt id','')}",
            f"Namn: {kontaktinfo.get('Namn','')}",
            f"Företag: {kontaktinfo.get('Företag','')}",
            f"Telefon: {kontaktinfo.get('Telefon','')}",
            f"E-post: {kontaktinfo.get('E-post','')}",
            f"Funktion: {kontaktinfo.get('Funktion','')}",
        ]
        txt = "   |   ".join(row)
        if len(txt) > 110:
            mid = len(row)//2
            pdf.drawString(margin_x, y, "   |   ".join(row[:mid])); y -= 14
            pdf.drawString(margin_x, y, "   |   ".join(row[mid:])); y -= 8
        else:
            pdf.drawString(margin_x, y, txt); y -= 14

        def ensure_space(need:int):
            nonlocal y
            if y-need < 50:
                pdf.showPage()
                pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,width,height,fill=1,stroke=0)
                pdf.setFillColor(black); pdf.setFont("Helvetica",9)
                pdf.drawString(margin_x, height-40, title)
                y = height-60

        bar_bg = Color(0.91,0.92,0.94)
        bar_green = Color(0.30,0.69,0.31)
        bar_orange = Color(0.96,0.65,0.15)
        bar_blue = Color(0.23,0.51,0.96)

        for block in sections:
            ensure_space(30)
            pdf.setFont("Helvetica-Bold", h2); pdf.drawString(margin_x, y, block["title"]); y -= h2+6
            pdf.setFont("Helvetica", body)
            for p in block["text"].split("\n\n"):
                for ln in textwrap.wrap(p, width=95):
                    ensure_space(line_h); pdf.drawString(margin_x, y, ln); y -= line_h
                y -= 0
            for label, key, color in [("Chef","chef",bar_green), ("Överordnad chef","overchef",bar_orange), ("Medarbetare","medarbetare",bar_blue)]:
                val = int(results_map.get(block["key"],{}).get(key,0))
                maxv = block["max"]
                ensure_space(26)
                pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"{label}: {val} poäng"); y -= 12
                bar_w, bar_h = width-2*margin_x, 8
                pdf.setFillColor(bar_bg); pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
                fill_w = 0 if maxv==0 else bar_w*(val/maxv)
                pdf.setFillColor(color); pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
                pdf.setFillColor(black); y -= 14
            pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin_x, y, f"Max: {block['max']} poäng"); y -= 18

        pdf.showPage(); pdf.save(); buf.seek(0)
        return buf.getvalue()

    pdf_bytes = generate_pdf(PAGE_TITLE, SECTIONS, preset_scores, kontakt)
    st.download_button("Ladda ner PDF", data=pdf_bytes, file_name="självskattning_funktionellt_ledarskap.pdf", mime="application/pdf", type="primary")

    if st.button("◀ Tillbaka till startsidan"):
        st.session_state["page"] = "landing"

# =============================
# Router
# =============================
if "page" not in st.session_state:
    st.session_state["page"] = "landing"

page = st.session_state["page"]
if page == "landing":
    render_landing()
elif page == "id_page":
    render_id_page()
else:
    render_assessment()
