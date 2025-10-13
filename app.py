from io import BytesIO
import textwrap, secrets, string

import streamlit as st
import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black

# =============================
# Grundinställningar / tema
# =============================
st.set_page_config(
    page_title="Självskattning – Funktionellt ledarskap",
    page_icon="📄",
    layout="centered",
)

EGGSHELL = "#FAF7F0"
PRIMARY = "#EF4444"

# =============================
# Power Automate (HTTP-trigger) – "När en HTTP-begäran tas emot"
# =============================
FLOW_POST_URL  = st.secrets.get("FLOW_POST_URL", "")   # POST-endpoint som skriver till SharePoint
FLOW_FETCH_URL = st.secrets.get("FLOW_FETCH_URL", "")  # (valfritt) GET-endpoint som hämtar via uid


def flow_send(payload: dict) -> bool:
    """POST:a nyttolast till Power Automate-flödet. Returnerar True om 2xx."""
    if not FLOW_POST_URL:
        return False
    try:
        r = requests.post(FLOW_POST_URL, json=payload, timeout=20)
        return 200 <= r.status_code < 300
    except Exception:
        return False


def flow_fetch(uid: str) -> dict | None:
    """(Valfritt) Hämta resultat via uid från ett GET-flöde som returnerar JSON."""
    if not (FLOW_FETCH_URL and uid):
        return None
    try:
        r = requests.get(FLOW_FETCH_URL, params={"uid": uid}, timeout=20)
        if 200 <= r.status_code < 300:
            return r.json()
    except Exception:
        pass
    return None

# =============================
# Hjälpfunktioner
# =============================
def generate_unikt_id() -> str:
    """Skapar en 6-teckenskod med exakt 3 bokstäver (a–z, A–Z) och 3 siffror (0–9) i slumpmässig ordning."""
    letters = string.ascii_letters  # a-z + A-Z
    digits = string.digits          # 0-9
    pool = [secrets.choice(letters) for _ in range(3)] + [secrets.choice(digits) for _ in range(3)]
    # Fisher–Yates-shuffle med secrets.randbelow för kryptografiskt slump
    for i in range(len(pool) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        pool[i], pool[j] = pool[j], pool[i]
    return "".join(pool)

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
INSTR_CHEF = """**Chef**

Syftet med frågorna nedan är att du ska beskriva hur du kommunicerar med dina medarbetare i frågor som rör deras arbete.

Använd följande svarsskala:

**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.

Ange hur ofta du gör följande:"""
INSTR_EMP = """**Medarbetare**

Syftet med frågorna nedan är att du ska beskriva hur din chef kommunicerar med dig i frågor som rör ditt arbete.

Använd följande svarsskala:

**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.

Ange hur ofta din chef gör följande:"""
INSTR_OVER = """**Överordnad chef**

Syftet med frågorna nedan är att du ska beskriva hur din underställda chef kommunicerar i arbetsrelaterade frågor.

Använd följande svarsskala:

**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.

Ange hur ofta din underställda chef gör följande:"""

# =============================
# PDF (matcha webblayout 68/32, rundade kort, tre staplar, ingen tidsstämpel, 2 radbryt före rubriker)
# =============================

def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    def paint_bg():
        pdf.setFillColor(HexColor(EGGSHELL))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        pdf.setFillColor(black)

    def page_header():
        y = h - 60
        # två radbryt ovanför rubriken
        y -= 28*2
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(50, y, title)
        return y - 28

    paint_bg()
    y = page_header()

    # Kontakt – två rader, ingen tidsstämpel
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    line1 = "   |   ".join([
        f"Namn: {contact.get('Förnamn','')} {contact.get('Efternamn','')}",
        f"Företag: {contact.get('Företag','')}",
        f"Telefon: {contact.get('Telefon','')}",
    ])
    line2 = "   |   ".join([
        f"E-post: {contact.get('E-post','')}",
        f"Unikt id: {contact.get('Unikt id','')}",
    ])
    pdf.drawString(50, y, line1); y -= 14
    pdf.drawString(50, y, line2); y -= 24

    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage()
            paint_bg()
            y2 = page_header()
            return y2
        return y

    # 68/32 kolumner
    margin = 50
    content_w = w - 2*margin
    left_w    = content_w * 0.68
    right_w   = content_w - left_w
    right_x   = margin + left_w

    for s in sections:
        # Sidbryt innan Målinriktning
        if s["title"] == "Målinriktning":
            pdf.showPage(); paint_bg(); y = page_header()

        y = ensure(40)
        # H2
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y, s["title"]); y -= 20

        section_top = y

        # Beräkna vänsterkolumnhöjd för vertikal centrering av kort
        pdf.setFont("Helvetica", 11)
        # 1) Mät vänsterkolumnens höjd
        y_probe = section_top
        approx_chars = max(40, int(95 * (left_w / content_w)))
        for para in str(s["text"]).split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                y_probe -= 16
            y_probe -= 4
        left_span = section_top - y_probe

        # 2) Höger: resultatkort, vertikalt centrerat mot vänstertexten
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
        roles = [("Chef", "chef", HexColor("#22C55E")),
                 ("Överordnad chef", "overchef", HexColor("#F59E0B")),
                 ("Medarbetare", "medarbetare", HexColor("#3B82F6"))]
        pdf.setFont("Helvetica", 10)
        for label, key, col in roles:
            val = int(results_map.get(s["key"], {}).get(key, 0))
            mx  = int(s.get("max", 0))
            pdf.drawString(inner_x, cy, f"{label}: {val} poäng"); cy -= 12
            bar_w = card_w - 2*card_pad; bar_h = 10
            pdf.setFillColor(HexColor("#E9ECEF")); pdf.rect(inner_x, cy, bar_w, bar_h, fill=1, stroke=0)
            fill_w = 0 if mx == 0 else bar_w * (val / mx)
            pdf.setFillColor(col); pdf.rect(inner_x, cy, fill_w, bar_h, fill=1, stroke=0)
            pdf.setFillColor(black); cy -= 14
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(inner_x, card_y + card_pad, f"Max: {int(s.get('max',0))} poäng")

        # 3) Vänster: rita text inom 68 %
        pdf.setFont("Helvetica", 11)
        y_left_draw = section_top
        for para in str(s["text"]).split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                y = ensure(16)
                pdf.drawString(margin, y_left_draw, ln)
                y_left_draw -= 16
            y_left_draw -= 4

        # 4) Gå ned till nästa sektion
        y = min(y_left_draw, card_y) - 16

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

    base = st.session_state.get("kontakt", {"Förnamn":"", "Efternamn":"", "Namn":"", "Företag":"", "Telefon":"", "E-post":"", "Funktion":"Chef", "Unikt id":""})
    with st.form("landing_form"):
        c1, c2 = st.columns(2)
        with c1:
            first = st.text_input("Förnamn", value=base.get("Förnamn",""))
            tel   = st.text_input("Telefon", value=base.get("Telefon",""))
            fun   = st.selectbox("Funktion", ["Chef", "Överordnad chef", "Medarbetare"], index=["Chef","Överordnad chef","Medarbetare"].index(base.get("Funktion","Chef")))
        with c2:
            last  = st.text_input("Efternamn", value=base.get("Efternamn",""))
            fore  = st.text_input("Företag", value=base.get("Företag",""))
            mail  = st.text_input("E-post", value=base.get("E-post",""))

        start = st.form_submit_button("Starta", type="primary")

    if start:
        if not first.strip() or not mail.strip():
            st.warning("Fyll i minst **Förnamn** och **E-post**.")
            return
        full_name = (first.strip() + " " + last.strip()).strip()
        st.session_state["kontakt"] = {
            "Förnamn": first.strip(),
            "Efternamn": last.strip(),
            "Namn": full_name,
            "Företag": fore.strip(),
            "Telefon": tel.strip(),
            "E-post": mail.strip(),
            "Funktion": fun,
            "Unikt id": generate_unikt_id() if fun == "Chef" else base.get("Unikt id",""),
        }
        if fun == "Chef":
            st.session_state["chef_answers"] = [None]*len(CHEF_QUESTIONS)
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
        else:
            st.session_state["page"] = "id_page"
        rerun()


def render_id_page():
    st.markdown("## Ange uppgifter för chefens självskattning")
    st.info("Detta steg gäller för **Överordnad chef** och **Medarbetare**.")

    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            chef_first = st.text_input("Chefens förnamn", value=base.get("Chefens förnamn", base.get("Förnamn","")))
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
            pressed = st.button("Nästa ▶", disabled=not full)
            if pressed:
                st.session_state[page_key] = page+1
                rerun()
        else:
            pressed = st.button("Skicka självskattning", type="primary", disabled=not full)
            if pressed:
                # Skicka till Power Automate-flöde (om FLOW_POST_URL är satt)
                k = st.session_state.get("kontakt", {})
                role = ("Chef" if answers_key == "chef_answers" else ("Medarbetare" if answers_key == "other_answers" else "Överordnad chef"))
                # summera delpoäng
                def part_sum(ans, key):
                    return sum(ans[i] for i in IDX_MAP[key] if isinstance(ans[i], int))
                parts = {
                    "lyssnande": part_sum(st.session_state[answers_key], "lyssnande"),
                    "aterkoppling": part_sum(st.session_state[answers_key], "aterkoppling"),
                    "malinriktning": part_sum(st.session_state[answers_key], "malinriktning"),
                }
                payload = {
                    "kontakt": {
                        "Förnamn": k.get("Förnamn",""),
                        "Efternamn": k.get("Efternamn",""),
                        "Företag": k.get("Företag",""),
                        "Telefon": k.get("Telefon",""),
                        "E-post": k.get("E-post",""),
                        "Funktion": k.get("Funktion",""),
                        "Unikt id": k.get("Unikt id",""),
                    },
                    "roll": role,
                    "answers": st.session_state[answers_key],
                    "scores": parts,
                }
                _ = flow_send(payload)
                # Gå vidare
                st.session_state["page"] = on_submit_page
                rerun()


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
    # Om resultatsidan öppnas via URL med ?uid=..., hämta via GET-endpoint och populera (om konfigurerat)
    qp = st.experimental_get_query_params()
    uid_qp = (qp.get("uid", [None])[0])
    if uid_qp and ("scores" not in st.session_state or not st.session_state.get("kontakt")):
        data = flow_fetch(uid_qp)
        if isinstance(data, dict):
            k = data.get("kontakt", {})
            s = data.get("scores", {})
            if k:
                st.session_state["kontakt"] = k
            if s:
                st.session_state["scores"] = s

    # Summera scorekartor
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

    st.markdown(f"# {PAGE_TITLE}")

    # Kontakt: 2×3 grid (Namn, Företag / E-post, Telefon / Funktion, Unikt id)
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    base = st.session_state.get("kontakt", {})
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Förnamn", value=base.get("Förnamn",""), disabled=True)
            st.text_input("Telefon", value=base.get("Telefon",""), disabled=True)
            st.selectbox(
                "Funktion",
                ["Chef", "Överordnad chef", "Medarbetare"],
                index=["Chef","Överordnad chef","Medarbetare"].index(base.get("Funktion","Chef")),
                disabled=True,
            )
        with c2:
            st.text_input("Efternamn", value=base.get("Efternamn",""), disabled=True)
            st.text_input("Företag", value=base.get("Företag",""), disabled=True)
            st.text_input("E-post", value=base.get("E-post",""), disabled=True)
        st.text_input("Unikt id", value=base.get("Unikt id",""), disabled=True)

    # Linje före sektionerna
    st.markdown("---")

    # Sektioner 68/32 med centrerade kort
    for s in SECTIONS:
        left, right = st.columns([0.68, 0.32])
        with left:
            st.header(s["title"])
            for p in s["text"].split("\n\n"): 
                st.write(p)
        with right:
            key, mx = s["key"], s["max"]
            chef = int(scores.get(key,{}).get("chef",0))
            over = int(scores.get(key,{}).get("overchef",0))
            med  = int(scores.get(key,{}).get("medarbetare",0))

            st.markdown("<div class='right-wrap'>", unsafe_allow_html=True)
            card = [f"<div class='res-card'>"]
            def bar(lbl, val, maxv, cls):
                pct = 0 if maxv==0 else (val/maxv)*100
                return [
                    f"<span class='role-label'>{lbl}: {val} poäng</span>",
                    f"<div class='barbg'><span class='barfill {cls}' style='width:{pct:.0f}%'></span></div>",
                ]
            card += bar("Chef", chef, mx, "bar-green")
            card += bar("Överordnad chef", over, mx, "bar-orange")
            card += bar("Medarbetare", med, mx, "bar-blue")
            card += [f"<div class='maxline'>Max: {mx} poäng</div>", "</div>"]
            st.markdown("\n".join(card), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # PDF
    k = st.session_state.get("kontakt", {})
    pdf_bytes = build_pdf(PAGE_TITLE, SECTIONS, scores, k)
    pdf_name = f"Självskattning - {(k.get('Förnamn') or '')} {(k.get('Efternamn') or '')} - {k.get('Företag') or 'Företag'}.pdf"
    st.download_button("Ladda ner PDF", data=pdf_bytes, file_name=pdf_name, mime="application/pdf", type="primary")

    # Dela-länk till resultatsidan via URL med uid
    uid_share = k.get("Unikt id")
    if uid_share:
        st.experimental_set_query_params(uid=uid_share)
        st.info(f"Dela denna länk för att se resultatet igen: ?uid={uid_share}")

    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"
        rerun()

# =============================
# CSS (dubbla klamrar i f-string)
# =============================
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

      /* Resultatkort (högerkolumn 32%) */
      .section-row {{ display:grid; grid-template-columns: 0.68fr 0.32fr; column-gap:24px; align-items:center; }}
      .right-wrap {{ display:flex; align-items:center; justify-content:center; }}
      .res-card {{ max-width:380px; width:100%; padding:16px 18px; border:1px solid rgba(0,0,0,.12);
                   border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.08); background:#fff; }}
      .role-label {{ font-size:13px; color:#111827; margin:10px 0 6px 0; display:block; font-weight:600; }}
      .barbg {{ width:100%; height:10px; background:#E9ECEF; border-radius:6px; overflow:hidden; }}
      .barfill {{ height:10px; display:block; }}
      .bar-green {{ background:#22C55E; }}
      .bar-orange {{ background:#F59E0B; }}
      .bar-blue {{ background:#3B82F6; }}
      .maxline {{ font-size:13px; color:#374151; margin-top:12px; font-weight:600; }}

      /* Download-knapp */
      .stDownloadButton>button {{ background:{PRIMARY}; border-color:{PRIMARY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

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
