from io import BytesIO
from datetime import datetime
import textwrap, secrets, string

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black

# ==================================================
# Bas / tema
# ==================================================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

EGGSHELL = "#FAF7F0"
PRIMARY = "#EF4444"

# --------------------------------------------------
# Hjälpare
# --------------------------------------------------

def rerun():
    st.experimental_rerun()

# ID-generator

def _rand(n=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

# --------------------------------------------------
# Frågebank (exempel)
# --------------------------------------------------
SECTIONS = [
    {"key": "aktivt_lyssnande", "title": "Aktivt lyssnande", "max": 49,
     "text": (
         "I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på "
         "den djupaste kompetensen och lösningarna på verksamhetens utmaningar.

"
         "Därför är aktivt lyssnande en av chefens viktigaste färdigheter...

"
         "Genom att agera på det du hör stärker du engagemang, förtroende och delaktighet."
     ),
     "questions": [
         "Jag visar intresse när medarbetare berättar om sitt arbete.",
         "Jag summerar vad jag hört för att säkerställa att jag förstått.",
         "Jag ställer följdfrågor som fördjupar bilden.",
         "Jag bjuder in till dialog i beslut.",
         "Jag agerar på relevant information från teamet.",
         "Jag efterfrågar olika perspektiv i gruppen.",
         "Jag ger utrymme för andra att tala till punkt.",
     ],
    },
]

PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

# --------------------------------------------------
# Komponent: 4-sidig enkät (5 frågor/sida)
# --------------------------------------------------

def render_survey_core(title: str, instruction_md: str, questions: list[str],
                       answers_key: str, page_key: str, on_submit_page: str):
    st.markdown(f"## {title}")
    st.markdown(f"<div class='note'>{instruction_md}</div>", unsafe_allow_html=True)
    st.caption("Svara på varje påstående på en skala 1–7. Du måste besvara alla frågor på sidan för att gå vidare.")

    if answers_key not in st.session_state:
        st.session_state[answers_key] = [None]*len(questions)
    answers = st.session_state[answers_key]

    page = st.session_state.get(page_key, 0)
    per_page = 5
    start_idx = page*per_page
    end_idx   = min(start_idx+per_page, len(questions))

    for i in range(start_idx, end_idx):
        st.markdown(f"**{i+1}. {questions[i]}**")
        current = answers[i]
        idx = None
        if isinstance(current, int) and 1 <= current <= 7:
            idx = [1,2,3,4,5,6,7].index(current)
        choice = st.radio("", [1,2,3,4,5,6,7], index=idx, horizontal=True,
                          label_visibility="collapsed", key=f"{answers_key}_{i}")
        st.session_state[answers_key][i] = choice
        if i < end_idx-1:
            st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if page > 0 and st.button("◀ Tillbaka", key=f"back_{page}"):
            st.session_state[page_key] = page - 1
            rerun()
    with col2:
        slice_vals = st.session_state[answers_key][start_idx:end_idx]
        full = all(isinstance(v, int) and 1 <= v <= 7 for v in slice_vals)
        if end_idx < len(questions):
            pressed = st.button("Nästa ▶", disabled=not full, key=f"next_{page}")
            if pressed:
                st.session_state[page_key] = page + 1
                rerun()
        else:
            pressed = st.button("Skicka självskattning", type="primary", disabled=not full, key="submit_survey")
            if pressed:
                st.session_state["page"] = on_submit_page
                rerun()

# --------------------------------------------------
# LANDNING
# --------------------------------------------------

def render_landing():
    st.markdown("# Självskattning – Funktionellt ledarskap")
    st.write("Fyll i dina uppgifter och starta självskattningen.")

    if "kontakt" not in st.session_state:
        st.session_state["kontakt"] = {"Namn":"", "Företag":"", "Funktion":"Chef",
                                        "E-post":"", "Telefon":"", "Unikt id": _rand()}
    k = st.session_state["kontakt"]

    with st.form("landing_form"):
        k["Namn"] = st.text_input("Namn", k["Namn"])    
        k["Företag"] = st.text_input("Företag", k["Företag"]) 
        k["Funktion"] = st.selectbox("Funktion", ["Chef","Medarbetare","Överordnad chef"], index=["Chef","Medarbetare","Överordnad chef"].index(k["Funktion"]))
        k["E-post"] = st.text_input("E-post", k["E-post"]) 
        k["Telefon"] = st.text_input("Telefon", k["Telefon"]) 
        col1, col2 = st.columns([1,1])
        with col1:
            go = st.form_submit_button("Starta")
        with col2:
            st.caption(f"Ditt id: {k['Unikt id']}")
    st.session_state["kontakt"] = k

    if 'scores' not in st.session_state:
        st.session_state['scores'] = {SECTIONS[0]['key']:{'chef':0,'overchef':0,'medarbetare':0}}

    if go:
        if k["Funktion"] == "Chef":
            st.session_state["page"] = "chef_survey"
        elif k["Funktion"] == "Medarbetare":
            st.session_state["page"] = "id_page"
        else:
            st.session_state["page"] = "id_page"
        rerun()

# --------------------------------------------------
# ID-sida (för Medarbetare/Överordnad chef)
# --------------------------------------------------

def render_id_page():
    st.markdown("## Ditt unika id")
    st.info(f"Använd detta id när du startar enkäten: **{st.session_state['kontakt']['Unikt id']}**")
    if st.button("Starta enkäten"):
        st.session_state["page"] = "other_survey"
        rerun()

# --------------------------------------------------
# Enkäter
# --------------------------------------------------

def render_chef_survey():
    q = SECTIONS[0]["questions"]
    render_survey_core("Självskattning – Chef", "Svara på frågorna nedan.", q,
                       "chef_answers", "chef_page", "assessment")
    # Poängsummering (enkel):
    if "chef_answers" in st.session_state:
        st.session_state['scores'][SECTIONS[0]['key']]['chef'] = sum(v or 0 for v in st.session_state['chef_answers'])


def render_other_survey():
    q = SECTIONS[0]["questions"]
    render_survey_core("Självskattning", "Svara på frågorna nedan.", q,
                       "other_answers", "other_page", "thankyou")
    if "other_answers" in st.session_state:
        role = st.session_state['kontakt']['Funktion']
        key = 'overchef' if role == 'Överordnad chef' else 'medarbetare'
        st.session_state['scores'][SECTIONS[0]['key']][key] = sum(v or 0 for v in st.session_state['other_answers'])

# --------------------------------------------------
# Resultat / PDF
# --------------------------------------------------

def _contact_block(base: dict):
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="contact-card">
          <div class="contact-grid">
            <div><div class="label">Namn</div><div class="pill">{base.get('Namn','')}</div></div>
            <div><div class="label">Företag</div><div class="pill">{base.get('Företag','')}</div></div>
            <div><div class="label">E-post</div><div class="pill">{base.get('E-post','')}</div></div>
            <div><div class="label">Telefon</div><div class="pill">{base.get('Telefon','')}</div></div>
            <div><div class="label">Funktion</div><div class="pill">{base.get('Funktion','')}</div></div>
            <div><div class="label">Unikt id</div><div class="pill">{base.get('Unikt id','')}</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assessment():
    st.markdown("# Resultat")
    base = st.session_state.get("kontakt", {})
    _contact_block(base)
    st.markdown("---")

    # 68/32 layout – text + kort
    s = SECTIONS[0]
    scores_map = st.session_state['scores'][s['key']]
    chef, over, med = scores_map['chef'], scores_map['overchef'], scores_map['medarbetare']

    # vänster (text)
    left_html = [f"<div><h2 class='sec-h2'>{s['title']}</h2>"]
    for p in s["text"].split("

"):
        left_html.append(f"<p>{p}</p>")
    left_html.append("</div>")

    def bar_html(lbl, val, maxv, cls):
        pct = 0 if maxv==0 else (val/maxv)*100
        return (f"<span class='role-label'>{lbl}: {val} poäng</span>"
                f"<div class='barbg'><span class='barfill {cls}' style='width:{pct:.0f}%'></span></div>")

    right_html = ["<div class='right-wrap'><div class='res-card'>"]
    right_html.append(bar_html("Chef", chef, s['max'], "bar-green"))
    right_html.append(bar_html("Överordnad chef", over, s['max'], "bar-orange"))
    right_html.append(bar_html("Medarbetare", med, s['max'], "bar-blue"))
    right_html.append(f"<div class='maxline'>Max: {s['max']} poäng</div></div></div>")

    section_html = ("<div class='section-row'>"
                    f"<div>{''.join(left_html)}</div>"
                    f"<div>{''.join(right_html)}</div>"
                    "</div>")
    st.markdown(section_html, unsafe_allow_html=True)

    # PDF-knapp
    pdf_bytes = build_pdf(PAGE_TITLE, SECTIONS, st.session_state['scores'], base)
    pdf_name = f"Självskattning - {base.get('Namn') or 'Person'} - {base.get('Företag') or 'Företag'}.pdf"
    st.download_button("Ladda ner PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf", type="primary")
    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"
        rerun()

# --------------------------------------------------
# Tack
# --------------------------------------------------

def render_thankyou():
    st.success("Tack! Ditt svar har registrerats.")
    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"
        rerun()

# --------------------------------------------------
# PDF-byggare (förenklad – matchar 68/32 och tre staplar, 2 radbryt före rubriker)
# --------------------------------------------------

def build_pdf(title, sections, scores, kontakt: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    margin = 40

    def page_header(pdf, title):
        y = h - 60
        y -= 28*2  # två radbryt före rubriken
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(margin, y, title)
        return y - 28

    # Sida 1 – kontakt + första sektionen
    y = page_header(pdf, title)

    # Kontakt (två rader, ingen tidsstämpel)
    pdf.setFont("Helvetica", 11)
    name_company = f"{kontakt.get('Namn','')} — {kontakt.get('Företag','')}"
    role_email = f"{kontakt.get('Funktion','')} — {kontakt.get('E-post','')}"
    pdf.drawString(margin, y, name_company); y -= 16
    pdf.drawString(margin, y, role_email); y -= 12

    pdf.line(margin, y, w - margin, y); y -= 16

    # En sektion (exempel) med 68/32
    s = sections[0]
    left_w = (w - 2*margin) * 0.68
    right_w = (w - 2*margin) * 0.32

    # Vänstertext
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, y, s['title']); y -= 18
    pdf.setFont("Helvetica", 11)

    y_text = y
    for para in s['text'].split("

"):
        for ln in textwrap.wrap(para, width=90):
            pdf.drawString(margin, y_text, ln); y_text -= 14
        y_text -= 6
    left_height = (y - y_text)

    # Högerkort
    card_h = 120
    card_y = y - (left_height/2 + card_h/2)
    card_x = margin + left_w + 18

    pdf.roundRect(card_x, card_y, right_w-18, card_h, 10, stroke=1, fill=0)
    # Staplar
    def bar(y0, label, value, maxv):
        pdf.setFont("Helvetica", 10)
        pdf.drawString(card_x + 10, y0+22, f"{label}: {value} poäng")
        bg_y = y0+8
        pdf.setFillColor(HexColor("#E5E7EB")); pdf.rect(card_x + 10, bg_y, right_w-38, 6, fill=1, stroke=0)
        pct = 0 if maxv==0 else (value/maxv)*(right_w-38)
        pdf.setFillColor(HexColor("#22C55E"))
        pdf.rect(card_x + 10, bg_y, pct, 6, fill=1, stroke=0)
        pdf.setFillColor(black)

    sc = scores[s['key']]
    bar(card_y + 72, "Chef", sc.get('chef',0), s['max'])
    bar(card_y + 42, "Överordnad chef", sc.get('overchef',0), s['max'])
    bar(card_y + 12, "Medarbetare", sc.get('medarbetare',0), s['max'])

    pdf.setFont("Helvetica", 10)
    pdf.drawString(card_x + 10, card_y - 10, f"Max: {s['max']} poäng")

    # Sidbryt innan Målinriktning (om vi hade fler sektioner)
    pdf.showPage()
    y = page_header(pdf, title)

    pdf.save()
    buf.seek(0)
    return buf.getvalue()

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown(
    f"""
    <style>
      body {{ background: {EGGSHELL}; }}
      .note {{ color:#374151; background:#FFF7ED; border:1px solid #FED7AA; padding:10px 12px; border-radius:8px; }}

      .section-row {{ display:grid; grid-template-columns: 0.68fr 0.32fr; column-gap:24px; align-items:center; }}
      .sec-h2 {{ font-size: 22px; font-weight: 700; margin: 10px 0 12px 0; }}

      .res-card {{ max-width:380px; width:100%; padding:16px 18px; border:1px solid rgba(0,0,0,.12);
                   border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.08); background:#fff; margin-top:12px; }}
      .role-label {{ display:block; font-size:13px; color:#111827; margin: 2px 0 6px; }}
      .barbg {{ height:6px; border-radius:999px; background:#E5E7EB; margin-bottom:10px; }}
      .barfill {{ display:block; height:6px; border-radius:999px; }}
      .bar-green {{ background:#22C55E; }}
      .bar-orange {{ background:#F59E0B; }}
      .bar-blue {{ background:#3B82F6; }}
      .maxline {{ font-size:13px; color:#374151; margin-top:12px; font-weight:600; }}

      .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}
      .contact-card {{ background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:12px; padding:12px 14px; box-shadow:0 4px 16px rgba(0,0,0,.06); }}
      .contact-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; }}
      .contact-grid .label {{ font-size:12px; color:#6B7280; margin-bottom:4px; }}
      .pill {{ background:#F8FAFC; padding:10px 12px; border-radius:8px; border:1px solid rgba(0,0,0,.06); }}

      .stDownloadButton>button {{ background:{PRIMARY}; border-color:{PRIMARY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================================================
# Router – starta alltid på landningssidan
# ==================================================
if "page" not in st.session_state or st.session_state["page"] not in {
    "landing","id_page","chef_survey","other_survey","assessment","thankyou"
}:
    st.session_state["page"] = "landing"

page = st.session_state["page"]
if page == "landing":
    render_landing()
elif page == "id_page":
    render_id_page()
elif page == "chef_survey":
    render_chef_survey()
elif page == "other_survey":
    render_other_survey()
elif page == "thankyou":
    render_thankyou()
else:
    render_assessment()
