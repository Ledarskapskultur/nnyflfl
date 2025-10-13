from io import BytesIO
from datetime import datetime
import string, secrets, textwrap

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# Grundinställningar / tema
# =============================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

EGGSHELL = "#FAF7F0"
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {EGGSHELL}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      .stMarkdown h2 {{ font-size: 20px; font-weight: 700; margin: 26px 0 10px 0; }}
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}

      /* Hero */
      .hero {{ text-align:center; padding:34px 28px; background:#fff;
               border-radius:14px; border:1px solid rgba(0,0,0,.08); box-shadow:0 6px 20px rgba(0,0,0,.06); }}

      /* Kontaktkort */
      .contact-card {{ background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:12px; padding:12px 14px; box-shadow:0 4px 16px rgba(0,0,0,.06); }}
      .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}
      .contact-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; }}
      .contact-grid .label {{ font-size:12px; color:#6B7280; margin-bottom:4px; }}
      .pill {{ background:#F8FAFC; padding:10px 12px; border-radius:8px; border:1px solid rgba(0,0,0,.06); }}
      .stTextInput>div>div>input {{ background:#F8FAFC; }}

      /* Resultatkort (högerkolumn 32%) */
      .right-wrap {{ display:flex; align-items:flex-start; justify-content:center; }}
      .res-card {{ max-width:380px; width:100%; padding:16px 18px; border:1px solid rgba(0,0,0,.12);
                   border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.08); background:#fff; }}
      .role-label {{ font-size:13px; color:#111827; margin:10px 0 6px 0; display:block; font-weight:600; }}
      .barbg {{ width:100%; height:10px; background:#E9ECEF; border-radius:6px; overflow:hidden; }}
      .barfill {{ height:10px; display:block; }}
      .bar-green {{ background:#4CAF50; }}
      .bar-orange {{ background:#F5A524; }}
      .bar-blue {{ background:#3B82F6; }}
      .maxline {{ font-size:13px; color:#374151; margin-top:12px; font-weight:600; }}

      /* Luta ned resultatkortet en aning för bättre balans */
      .res-card {{ margin-top:12px; }}

      /* Sektionstitel (ersätter st.header för exakt spacing) */
      .sec-h2 {{ font-size: 22px; font-weight: 700; margin: 10px 0 12px 0; }}

      /* Sektion med grid för vertikal centrering */
      .section-row {{ display:grid; grid-template-columns: 0.68fr 0.32fr; column-gap:24px; align-items:center; }}

      /* Info-ruta */
      .note {{ border-left: 6px solid #3B82F6; background:#EAF2FF; color:#0F172A;
               padding:14px 16px; border-radius:10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Hjälpfunktioner
# =============================
def generate_unikt_id(n=8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# =============================
# Innehållsdata (texter/sektioner)
# =============================
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "max": 49,  # 7 frågor
        "text": """I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och lösningarna på verksamhetens utmaningar.

Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.

Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både engagemang, förtroende och delaktighet."""
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "max": 56,  # 8 frågor
        "text": """Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och förväntade beteenden skapar du trygghet och fokus i arbetet.

Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du önskvärda beteenden och hjälper dina medarbetare att lyckas.

I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser visar ledarskap på riktigt."""
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "max": 35,  # 5 frågor
        "text": """Målinriktat ledarskap handlar om att ge tydliga ramar – tid, resurser och ansvar – så att medarbetare kan arbeta effektivt och med trygghet. Tydliga och inspirerande mål skapar riktning och hjälper alla att förstå vad som är viktigt just nu.

Som chef handlar det om att formulera mål som går att tro på, och att tydliggöra hur de ska nås. När du delegerar ansvar och befogenheter visar du förtroende och skapar engagemang. Målen blir då inte bara något att leverera på – utan något att vara delaktig i.

Uppföljning är nyckeln. Genom att uppmärksamma framsteg, ge återkoppling och fira resultat förstärker du både prestation och motivation."""
    },
]

# =============================
# Frågebatterier (20 frågor) + indexgrupper
# =============================
CHEF_QUESTIONS = [
    "Efterfrågar deras förslag när det gäller hur arbetet kan förbättras",
    "Efterfrågar deras idéer när det gäller planering av arbetet",
    "Uppmuntrar dem att uttrycka eventuella farhågor när det gäller arbetet",
    "Uppmuntrar dem att komma med förbättringsförslag för verksamheten",
    "Uppmuntrar dem att uttrycka idéer och förslag",
    "Använder dig av deras förslag när du fattar beslut som berör dem",
    "Överväger deras idéer även när du inte håller med",
    "Talar om deras arbete som meningsfullt och viktigt",
    "Formulerar inspirerande målsättningar för deras arbete",
    "Beskriver hur deras arbete bidrar till viktiga värderingar och ideal",
    "Pratar på ett inspirerande sätt om deras arbete",
    "Beskriver hur deras arbete bidrar till verksamhetens mål",
    "Är tydlig med hur deras arbete bidrar till verksamhetens effektivitet",
    "Tillhandahåller information som visar på betydelsen av deras arbete",
    "Använder fakta och logik när du beskriver betydelsen av deras arbete",
    "Beskriver vilka arbetsuppgifter du vill att de utför",
    "Beskriver tidsplaner för de arbetsuppgifter du delegerar till dem",
    "Kommunicerar verksamhetens målsättningar på ett tydligt sätt",
    "Är tydlig med vad du förväntar dig av dem",
    "Ser till att dina medarbetares arbete samordnas",
]
EMP_QUESTIONS = CHEF_QUESTIONS[:]  # samma formuleringar men ur medarbetarperspektiv
OVER_QUESTIONS = [
    "Efterfrågar andras förslag när det gäller hur hens verksamhet kan förbättras",
    "Efterfrågar andras idéer när det gäller planering av hens verksamhet",
    "Uppmuntrar andra att uttrycka eventuella farhågor när det gäller hens verksamhet",
    "Uppmuntrar andra att komma med förbättringsförslag för hens verksamhet",
    "Uppmuntrar andra att uttrycka idéer och förslag",
    "Använder sig av andras förslag när hen fattar beslut som berör dem",
    "Överväger andras idéer även när hen inte håller med om dem",
    "Talar om sin verksamhet som meningsfull och viktig",
    "Formulerar inspirerande målsättningar",
    "Beskriver viktiga värderingar och ideal",
    "Pratar på ett inspirerande sätt",
    "Beskriver sin verksamhets mål",
    "Är tydlig med sin verksamhets effektivitet",
    "Tillhandahåller relevant information",
    "Använder fakta och logik",
    "Beskriver vem som är ansvarig för vad",
    "Beskriver tidsplaner för de arbetsuppgifter som ska göras",
    "Kommunicerar verksamhetens målsättningar på ett tydligt sätt",
    "Är tydlig med vad hen förväntar sig av andra",
    "Ser till att arbetet samordnas",
]

IDX_MAP = {
    "lyssnande": list(range(0, 7)),
    "aterkoppling": list(range(7, 15)),
    "malinriktning": list(range(15, 20)),
}

# Instruktioner
INSTR_CHEF = (
    "**Chef**\n\n"
    "Syftet med frågorna nedan är att du ska beskriva hur du kommunicerar med dina medarbetare i frågor som rör deras arbete.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta du gör följande:"
)
INSTR_EMP = (
    "**Medarbetare**\n\n"
    "Syftet med frågorna nedan är att du ska beskriva hur din chef kommunicerar med dig i frågor som rör ditt arbete.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta din chef gör följande:"
)
INSTR_OVER = (
    "**Överordnad chef**\n\n"
    "Syftet med frågorna nedan är att du ska beskriva hur din underställda chef kommunicerar i arbetsrelaterade frågor.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta din underställda chef gör följande:"
)

# =============================
# PDF (matcha webblayout 68/32, kort till höger, ingen tidsstämpel)
# =============================
def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    def paint_bg():
        pdf.setFillColor(HexColor(EGGSHELL))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        pdf.setFillColor(black)

    paint_bg()
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    margin = 50
    y = h - 60
    y -= 28*2

    # H1 (ingen tidsstämpel)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(margin, y, title)
    y -= 28

    # Kontaktuppgifter – två rader i ordning: Namn|Företag|Telefon  /  E-post|Unikt id
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
    pdf.drawString(margin, y, line2); y -= 24
    y -= 6  # lite extra luft så första H2 hamnar lägre

    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage()
            paint_bg()
            yy = h - 60
            yy -= 28*2
            pdf.setFont("Helvetica-Bold", 22)
            pdf.drawString(margin, yy, title)
            y = yy - 28

    # Färger progressbars
    bar_bg  = Color(0.91, 0.92, 0.94)    # #E9ECEF
    col_chef = Color(0.30, 0.69, 0.31)   # #4CAF50
    col_over = Color(0.96, 0.65, 0.15)   # #F5A524
    col_med  = Color(0.23, 0.51, 0.96)   # #3B82F6

    # 68/32 kolumner
    content_w = w - 2*margin
    left_w    = content_w * 0.68
    right_w   = content_w - left_w
    right_x   = margin + left_w

    for s in sections:
        # Sidbryt före Målinriktning
        if s["title"] == "Målinriktning":
            pdf.showPage()
            paint_bg()
            yy = h - 60
            yy -= 28*2
            pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, yy, title)
            y = yy - 28

        ensure(40)
        # H2
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y, s["title"])
        y -= 20

        section_top = y  # brödtextens topp

        # Beräkna vänsterkolumnens höjd för att centrera kortet vertikalt
        approx_chars = max(40, int(95 * (left_w / content_w)))
        y_probe = section_top
        for para in str(s["text"]).split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                y_probe -= 16
            y_probe -= 4
        left_span = section_top - y_probe

        card_pad = 10
        card_w   = right_w - 10
        per_role = 12 + 10 + 14
        card_h   = card_pad + 3*per_role + 10 + card_pad
        card_y   = section_top - (left_span/2 + card_h/2)

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

        # Vänster: brödtext inom 68 %
        pdf.setFont("Helvetica", 11)
        y_left = section_top
        approx_chars = max(40, int(95 * (left_w / content_w)))
        for para in str(s["text"]).split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                ensure(16); pdf.drawString(margin, y_left, ln); y_left -= 16
            y_left -= 4

        y = min(y_left, card_y) - 16

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()

# =============================
# Sidor
# =============================
def render_landing():
    st.markdown(
        """
        <div class="hero">
          <h1>Självskattning – Funktionellt ledarskap</h1>
          <p>Fyll i dina uppgifter nedan och starta självskattningen.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    base = st.session_state.get("kontakt", {"Namn":"", "Företag":"", "Telefon":"", "E-post":"", "Funktion":"Chef", "Unikt id":""})
    with st.form("landing_form"):
        c1, c2 = st.columns(2)
        with c1:
            namn = st.text_input("Namn", value=base["Namn"])
            tel  = st.text_input("Telefon", value=base["Telefon"])
            fun  = st.selectbox("Funktion", ["Chef", "Överordnad chef", "Medarbetare"], index=["Chef","Överordnad chef","Medarbetare"].index(base["Funktion"]))
        with c2:
            fore = st.text_input("Företag", value=base["Företag"])
            mail = st.text_input("E-post", value=base["E-post"])

        start = st.form_submit_button("Starta", type="primary")

    if start:
        if not namn.strip() or not mail.strip():
            st.warning("Fyll i minst **Namn** och **E-post**.")
            return
        # Spara
        st.session_state["kontakt"] = {
            "Namn": namn.strip(),
            "Företag": fore.strip(),
            "Telefon": tel.strip(),
            "E-post": mail.strip(),
            "Funktion": fun,
            "Unikt id": generate_unikt_id() if fun == "Chef" else "",
        }
        # Startflöde
        if fun == "Chef":
            st.session_state["chef_answers"] = [None]*len(CHEF_QUESTIONS)
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
        else:
            st.session_state["page"] = "id_page"  # unikt id + (ev) chefens förnamn
        rerun()

def render_id_page():
    st.markdown("## Ange uppgifter för chefens självskattning")
    st.info("Detta steg gäller för **Överordnad chef** och **Medarbetare**.")

    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            chef_first = st.text_input("Chefens förnamn", value=base.get("Chefens förnamn",""))
            uid        = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write(""); st.write(f"**Din roll:** {base.get('Funktion','')}")

        ok = st.form_submit_button("Fortsätt", type="primary")

    if ok:
        if not chef_first.strip() or not uid.strip():
            st.warning("Fyll i både **Chefens förnamn** och **Unikt id**.")
            return
        st.session_state["kontakt"]["Chefens förnamn"] = chef_first.strip()
        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        if base.get("Funktion") == "Medarbetare":
            st.session_state["other_answers"] = [None]*len(EMP_QUESTIONS)
            st.session_state["other_page"] = 0
            st.session_state["page"] = "other_survey"
        else:
            st.session_state["over_answers"] = [None]*len(OVER_QUESTIONS)
            st.session_state["over_page"] = 0
            st.session_state["page"] = "over_survey"
        rerun()

    if st.button("◀ Tillbaka"):
        st.session_state["page"] = "landing"
        rerun()

# Gemensam enkät-renderare (4 sidor × 5 frågor)
def render_survey_core(title: str, instruction_md: str, questions: list[str], answers_key: str, page_key: str, on_submit_page: str):
    st.markdown(f"## {title}")
    st.markdown(f"<div class='note'>{instruction_md}</div>", unsafe_allow_html=True)
    st.caption("Svara på varje påstående på en skala 1–7. Du måste besvara alla frågor på sidan för att gå vidare.")

    answers = st.session_state.get(answers_key, [None]*len(questions))
    page = st.session_state.get(page_key, 0)
    per_page = 5
    start_idx = page*per_page
    end_idx   = start_idx+per_page

    for i in range(start_idx, end_idx):
        st.markdown(f"**{i+1}. {questions[i]}**")
        current = answers[i]
        idx = None
        if isinstance(current, int) and 1 <= current <= 7:
            idx = [1,2,3,4,5,6,7].index(current)
        st.radio("", [1,2,3,4,5,6,7], index=idx, horizontal=True, label_visibility="collapsed", key=f"{answers_key}_{i}")
        st.session_state[answers_key][i] = st.session_state.get(f"{answers_key}_{i}")
        if i < end_idx-1:
            st.divider()

    c1, c2 = st.columns(2)
    with c1:
        if page > 0 and st.button("◀ Tillbaka"):
            st.session_state[page_key] = page-1
            rerun()
    with c2:
        slice_vals = st.session_state[answers_key][start_idx:end_idx]
        full = all(isinstance(v, int) and 1 <= v <= 7 for v in slice_vals)
        if page < 3:
            (lambda pressed: (st.session_state.update({page_key: page+1}) or rerun()) if pressed else None)(
                st.button("Nästa ▶", disabled=not full, key=f"next_{page}")
            )
        else:
            (lambda pressed: (st.session_state.update({"page": on_submit_page}) or rerun()) if pressed else None)(
                st.button("Skicka självskattning", type="primary", disabled=not full, key="submit_survey")
            )

def render_chef_survey():
    render_survey_core("Självskattning (Chef)", INSTR_CHEF, CHEF_QUESTIONS, "chef_answers", "survey_page", "assessment")

def render_other_survey():
    render_survey_core("Självskattning (Medarbetare)", INSTR_EMP, EMP_QUESTIONS, "other_answers", "other_page", "thankyou")

def render_over_survey():
    render_survey_core("Självskattning (Överordnad chef)", INSTR_OVER, OVER_QUESTIONS, "over_answers", "over_page", "thankyou")

def render_thankyou():
    st.markdown(
        """
        <div class="hero">
          <h2>Tack för din medverkan!</h2>
          <p>Dina svar har registrerats. Du kan nu stänga sidan.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Gå till startsidan"):
        st.session_state["page"] = "landing"
        rerun()

def render_assessment():
    # Summera scorekartor
    scores = {"lyssnande":{}, "aterkoppling":{}, "malinriktning":{}}

    if "chef_answers" in st.session_state:
        a = st.session_state["chef_answers"]
        scores["lyssnande"]["chef"]     = sum(a[i] for i in IDX_MAP["lyssnande"]    if isinstance(a[i], int))
        scores["aterkoppling"]["chef"]  = sum(a[i] for i in IDX_MAP["aterkoppling"]  if isinstance(a[i], int))
        scores["malinriktning"]["chef"] = sum(a[i] for i in IDX_MAP["malinriktning"] if isinstance(a[i], int))

    if "other_answers" in st.session_state:
        a = st.session_state["other_answers"]
        scores["lyssnande"]["medarbetare"]     = sum(a[i] for i in IDX_MAP["lyssnande"]    if isinstance(a[i], int))
        scores["aterkoppling"]["medarbetare"]  = sum(a[i] for i in IDX_MAP["aterkoppling"]  if isinstance(a[i], int))
        scores["malinriktning"]["medarbetare"] = sum(a[i] for i in IDX_MAP["malinriktning"] if isinstance(a[i], int))

    if "over_answers" in st.session_state:
        a = st.session_state["over_answers"]
        scores["lyssnande"]["overchef"]     = sum(a[i] for i in IDX_MAP["lyssnande"]    if isinstance(a[i], int))
        scores["aterkoppling"]["overchef"]  = sum(a[i] for i in IDX_MAP["aterkoppling"]  if isinstance(a[i], int))
        scores["malinriktning"]["overchef"] = sum(a[i] for i in IDX_MAP["malinriktning"] if isinstance(a[i], int))

    st.session_state["scores"] = scores

    # Titel
    st.markdown(f"# {PAGE_TITLE}")

    # Kontakt (låsta fält)
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    base = st.session_state.get("kontakt", {})
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
          </div></div>
            <div><div class="label">Företag</div><div class="pill">{base.get('Företag','')}</div></div>
            <div><div class="label">Funktion</div><div class="pill">{base.get('Funktion','')}</div></div>
            <div><div class="label">E-post</div><div class="pill">{base.get('E-post','')}</div></div>
            <div><div class="label">Telefon</div><div class="pill">{base.get('Telefon','')}</div></div>
            <div><div class="label">Unikt id</div><div class="pill">{base.get('Unikt id','')}</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Lite luft så första H2 hamnar lägre (matchar PDF-känsla)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Sektioner 68/32
    for s in SECTIONS:
        key, mx = s["key"], s["max"]
        scores_map = st.session_state["scores"]
        chef = int(scores_map.get(key,{}).get("chef",0))
        over = int(scores_map.get(key,{}).get("overchef",0))
        med  = int(scores_map.get(key,{}).get("medarbetare",0))

        left_html = [f"<div><h2 class='sec-h2'>{s['title']}</h2>"]
        for p in s["text"].split("\n\n"):
            left_html.append(f"<p>{p}</p>")
        left_html.append("</div>")

        def bar_html(lbl, val, maxv, cls):
            pct = 0 if maxv==0 else (val/maxv)*100
            return (f"<span class='role-label'>{lbl}: {val} poäng</span>"
                    f"<div class='barbg'><span class='barfill {cls}' style='width:{pct:.0f}%'></span></div>")

        right_html = ["<div class='right-wrap'><div class='res-card'>"]
        right_html.append(bar_html("Chef", chef, mx, "bar-green"))
        right_html.append(bar_html("Överordnad chef", over, mx, "bar-orange"))
        right_html.append(bar_html("Medarbetare", med, mx, "bar-blue"))
        right_html.append(f"<div class='maxline'>Max: {mx} poäng</div></div></div>")

        section_html = ("<div class='section-row'>"
                        f"<div>{''.join(left_html)}</div>"
                        f"<div>{''.join(right_html)}</div>"
                        "</div>")
        st.markdown(section_html, unsafe_allow_html=True)

    # PDF
    st.divider()
    k = st.session_state.get("kontakt", {})
    pdf_bytes = build_pdf(PAGE_TITLE, SECTIONS, scores, k)
    pdf_name = f"Självskattning - {k.get('Namn') or 'Person'} - {k.get('Företag') or 'Företag'}.pdf"
    st.download_button("Ladda ner PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf", type="primary")

    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"
        rerun()

# =============================
# Router (starta alltid på landningssidan)
# =============================
if "page" not in st.session_state or st.session_state["page"] not in {
    "landing","id_page","chef_survey","other_survey","over_survey","assessment","thankyou"
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
elif page == "over_survey":
    render_over_survey()
elif page == "thankyou":
    render_thankyou()
else:
    render_assessment()
