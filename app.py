from io import BytesIO
from datetime import datetime
import os, textwrap, string, secrets, requests

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# Grundinställningar / tema
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

      .note {{ border-left: 6px solid #3B82F6; background:#EAF2FF; color:#0F172A;
               padding:14px 16px; border-radius:10px; }}

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
# Power Automate (valfritt)
# =============================
FLOW_LOOKUP_URL = os.getenv("FLOW_LOOKUP_URL", "").strip()  # {"action":"lookup","uniqueId": "..."} -> {found, name, company, email}
FLOW_LOG_URL    = os.getenv("FLOW_LOG_URL", "").strip()     # {"action":"log","uniqueId","firstName","role","timestamp"}

def safe_post(url: str, payload: dict):
    if not url:
        return False, None, "No URL configured"
    try:
        r = requests.post(url, json=payload, timeout=20)
        if 200 <= r.status_code < 300:
            try:
                return True, (r.json() if r.content else {}), None
            except Exception:
                return True, {}, None
        return False, None, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, None, str(e)

# =============================
# Innehåll & frågor
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

QUESTIONS = [
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

IDX_MAP = {
    "lyssnande": list(range(0, 7)),
    "aterkoppling": list(range(7, 15)),
    "malinriktning": list(range(15, 20)),
}

# Instruktionstexter (grafisk ruta ovanför enkäten)
INSTR_CHEF = (
    "**Chef**\n\n"
    "Syftet med frågorna nedan är att du ska beskriva hur du kommunicerar med dina medarbetare i frågor som rör deras arbete. "
    "Använd följande svarsskala: **1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**. "
    "Ange hur ofta **du** gör följande:"
)
INSTR_EMP = (
    "**Medarbetare/Överordnad chef**\n\n"
    "Syftet med frågorna nedan är att du ska beskriva hur din chef kommunicerar med dig i frågor som rör ditt arbete. "
    "Använd följande svarsskala: **1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**. "
    "Ange hur ofta **din chef** gör följande:"
)

# =============================
# Hjälpare
# =============================
def generate_unikt_id(n=8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def do_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def pdf_from_page(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
    pdf.setFillColor(black)

    margin = 50; y = h - 60
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")
    pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, y, title)
    pdf.setFont("Helvetica", 9); pdf.drawRightString(w - margin, y+4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
    y -= 28

    pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    row = [
        f"Unikt id: {kontaktinfo.get('Unikt id','')}",
        f"Namn: {kontaktinfo.get('Namn','')}",
        f"Företag: {kontaktinfo.get('Företag','')}",
        f"Telefon: {kontaktinfo.get('Telefon','')}",
        f"E-post: {kontaktinfo.get('E-post','')}",
        f"Funktion: {kontaktinfo.get('Funktion','')}",
    ]
    line = "   |   ".join(row)
    if len(line) > 110:
        mid = len(row)//2
        pdf.drawString(margin, y, "   |   ".join(row[:mid])); y -= 14
        pdf.drawString(margin, y, "   |   ".join(row[mid:])); y -= 8
    else:
        pdf.drawString(margin, y, line); y -= 14

    def ensure(n):
        nonlocal y
        if y - n < 50:
            pdf.showPage(); pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
            pdf.setFillColor(black); pdf.setFont("Helvetica",9); pdf.drawString(margin, h-40, title); y = h - 60

    bg = Color(0.91,0.92,0.94); green=Color(0.30,0.69,0.31); orange=Color(0.96,0.65,0.15); blue=Color(0.23,0.51,0.96)

    for s in sections:
        ensure(30)
        pdf.setFont("Helvetica-Bold", 14); pdf.drawString(margin, y, s["title"]); y -= 20
        pdf.setFont("Helvetica", 11)
        for para in s["text"].split("\n\n"):
            for ln in textwrap.wrap(para, width=95):
                ensure(16); pdf.drawString(margin, y, ln); y -= 16

        key, mx = s["key"], s["max"]
        for label, role, col in [("Chef","chef",green), ("Överordnad chef","overchef",orange), ("Medarbetare","medarbetare",blue)]:
            val = int(results_map.get(key,{}).get(role,0))
            ensure(26); pdf.setFont("Helvetica-Bold",10); pdf.drawString(margin, y, f"{label}: {val} poäng"); y -= 12
            bw, bh = w-2*margin, 8; pdf.setFillColor(bg); pdf.rect(margin, y, bw, bh, fill=1, stroke=0)
            fw = 0 if mx==0 else bw*(val/mx); pdf.setFillColor(col); pdf.rect(margin, y, fw, bh, fill=1, stroke=0)
            pdf.setFillColor(black); y -= 14

        pdf.setFont("Helvetica-Bold",10); pdf.drawString(margin, y, f"Max: {mx} poäng"); y -= 18

    pdf.showPage(); pdf.save(); buf.seek(0); return buf.getvalue()

# =============================
# Sidor
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
    d = st.session_state.get("kontakt", {"Namn":"","Företag":"","Telefon":"","E-post":"","Funktion":"Chef","Unikt id":""})
    with st.form("landing"):
        c1, c2 = st.columns([0.5, 0.5])
        with c1:
            namn = st.text_input("Namn", value=d["Namn"])
            tel  = st.text_input("Telefon", value=d["Telefon"])
            fun  = st.selectbox("Funktion", ["Chef","Överordnad chef","Medarbetare"],
                                index=["Chef","Överordnad chef","Medarbetare"].index(d["Funktion"]))
        with c2:
            fore = st.text_input("Företag", value=d["Företag"])
            mail = st.text_input("E-post", value=d["E-post"])
        start = st.form_submit_button("Starta", type="primary")

    if start:
        if not namn.strip() or not mail.strip():
            st.warning("Fyll i minst Namn och E-post.")
            return
        unikt_id = generate_unikt_id() if fun == "Chef" else ""
        st.session_state["kontakt"] = {
            "Namn": namn.strip(), "Företag": fore.strip(), "Telefon": tel.strip(),
            "E-post": mail.strip(), "Funktion": fun, "Unikt id": unikt_id
        }
        if fun == "Chef":
            st.session_state["chef_answers"] = [None] * len(QUESTIONS)
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
            do_rerun()
        else:
            st.session_state["page"] = "id_page"
            do_rerun()

def render_id_page():
    st.markdown("## Ange uppgifter för chefens självskattning")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")

    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            chef_first = st.text_input("Chefens förnamn", value=base.get("Chefens förnamn",""))
            uid = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write(""); st.write(f"**Din roll:** {base.get('Funktion','')}")
        ok = st.form_submit_button("Fortsätt", type="primary")

    if ok:
        if not chef_first.strip() or not uid.strip():
            st.warning("Fyll i både **Chefens förnamn** och **Unikt id**.")
            return

        # (valfritt) logga deltagande
        _ = safe_post(FLOW_LOG_URL, {
            "action": "log",
            "uniqueId": uid.strip(),
            "firstName": chef_first.strip(),
            "role": "overchef" if base.get("Funktion") == "Överordnad chef" else "medarbetare",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

        # (valfritt) hämta chefens namn via id
        looked_up = {}
        ok_lu, data_lu, _err = safe_post(FLOW_LOOKUP_URL, {"action":"lookup","uniqueId": uid.strip()})
        if ok_lu and data_lu and data_lu.get("found"):
            looked_up = data_lu

        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        st.session_state["kontakt"]["Chefens förnamn"] = chef_first.strip()
        if looked_up.get("name"):
            st.session_state["kontakt"]["Namn"] = looked_up["name"]
        if looked_up.get("company"):
            st.session_state["kontakt"]["Företag"] = looked_up["company"]
        if looked_up.get("email"):
            st.session_state["kontakt"]["E-post"] = looked_up["email"]

        # starta rätt enkät (för deltagare = överchef/medarbetare)
        st.session_state["other_answers"] = [None] * len(QUESTIONS)
        st.session_state["other_page"] = 0
        st.session_state["page"] = "other_survey"
        do_rerun()

    if st.button("◀ Tillbaka"):
        st.session_state["page"] = "landing"
        do_rerun()

# --- gemensamt enkät-render för 4 sidor × 5 frågor ---
def render_survey_core(title: str, instruction_md: str, answers_key: str, page_key: str):
    st.markdown(f"## {title}")

    # Instruktionsruta
    st.markdown(f"<div class='note'>{instruction_md}</div>", unsafe_allow_html=True)

    # liten caption
    st.caption("Svara på varje påstående på en skala 1–7. Du måste besvara alla frågor på sidan för att gå vidare.")

    if st.session_state.get("scroll_to_top"):
        st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)
        st.session_state["scroll_to_top"] = False

    ans = st.session_state.get(answers_key, [None]*len(QUESTIONS))
    page = st.session_state.get(page_key, 0)

    per_page = 5
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_slice = list(enumerate(QUESTIONS[start_idx:end_idx], start=start_idx+1))

    for i, q in current_slice:
        st.markdown(f"**{i}. {q}**")
        current_val = ans[i-1]
        idx = None
        if isinstance(current_val, int) and 1 <= current_val <= 7:
            idx = [1,2,3,4,5,6,7].index(current_val)
        st.radio("", [1,2,3,4,5,6,7], index=idx, horizontal=True, label_visibility="collapsed", key=f"{answers_key}_q_{i}")
        st.session_state[answers_key][i-1] = st.session_state.get(f"{answers_key}_q_{i}")
        if i != current_slice[-1][0]:
            st.divider()

    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if page > 0 and st.button("◀ Tillbaka"):
            st.session_state[page_key] = page - 1
            st.session_state["scroll_to_top"] = True
            do_rerun()
    with col2:
        page_answers = st.session_state[answers_key][start_idx:end_idx]
        all_filled = all(isinstance(v, int) and 1 <= v <= 7 for v in page_answers)
        if page < 3:
            if st.button("Nästa ▶", disabled=not all_filled):
                st.session_state[page_key] = page + 1
                st.session_state["scroll_to_top"] = True
                do_rerun()
        else:
            # sista sidan, spara och vidare
            if st.button("Skicka självskattning", type="primary", disabled=not all_filled):
                st.session_state["page"] = "assessment"
                do_rerun()

def render_chef_survey():
    render_survey_core(
        title="Självskattning (Chef)",
        instruction_md=INSTR_CHEF,
        answers_key="chef_answers",
        page_key="survey_page",
    )

def render_other_survey():
    # Titel sätts baserat på roll
    role = st.session_state.get("kontakt", {}).get("Funktion", "Medarbetare")
    title = "Självskattning (Medarbetare)" if role == "Medarbetare" else "Självskattning (Överordnad chef)"
    render_survey_core(
        title=title,
        instruction_md=INSTR_EMP,
        answers_key="other_answers",
        page_key="other_page",
    )

def render_assessment():
    # summera in eventuella svar från enkäterna
    scores = st.session_state.get("scores", {"lyssnande":{}, "aterkoppling":{}, "malinriktning":{}})

    # Chef-svar
    if "chef_answers" in st.session_state and isinstance(st.session_state["chef_answers"], list):
        a = st.session_state["chef_answers"]
        def ssum(idxs): return sum(a[i] for i in idxs if isinstance(a[i], int))
        scores["lyssnande"]["chef"]    = ssum(IDX_MAP["lyssnande"])
        scores["aterkoppling"]["chef"] = ssum(IDX_MAP["aterkoppling"])
        scores["malinriktning"]["chef"]= ssum(IDX_MAP["malinriktning"])

    # Medarbetare/Överordnad
    if "other_answers" in st.session_state and isinstance(st.session_state["other_answers"], list):
        a = st.session_state["other_answers"]
        def ssum(idxs): return sum(a[i] for i in idxs if isinstance(a[i], int))
        role = st.session_state.get("kontakt", {}).get("Funktion", "Medarbetare")
        key = "medarbetare" if role == "Medarbetare" else "overchef"
        scores["lyssnande"][key]     = ssum(IDX_MAP["lyssnande"])
        scores["aterkoppling"][key]  = ssum(IDX_MAP["aterkoppling"])
        scores["malinriktning"][key] = ssum(IDX_MAP["malinriktning"])

    st.session_state["scores"] = scores

    # ====== UI ======
    st.markdown(f"# {PAGE_TITLE}")

    # Kontaktuppgifter – låsta fält
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card contact-card'>", unsafe_allow_html=True)
        base = st.session_state.get("kontakt", {"Namn":"","Företag":"","Telefon":"","E-post":"","Funktion":"Chef","Unikt id":""})
        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
        with c1:
            st.text_input("Namn", value=base.get("Namn",""), disabled=True)
            st.text_input("E-post", value=base.get("E-post",""), disabled=True)
        with c2:
            st.text_input("Företag", value=base.get("Företag",""), disabled=True)
            st.text_input("Telefon", value=base.get("Telefon",""), disabled=True)
        with c3:
            st.text_input("Funktion", value=base.get("Funktion",""), disabled=True)
            st.text_input("Unikt id", value=base.get("Unikt id",""), disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Resultatkorten (68/32)
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
            card = [f"<div class='card res-card'>"]

            def bar(lbl, val, maxv, cls):
                pct = 0 if maxv==0 else val/maxv*100
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

    st.divider()
    st.caption("Ladda ner en PDF som speglar innehållet.")
    pdf_bytes = pdf_from_page(PAGE_TITLE, SECTIONS, scores, st.session_state.get("kontakt", {}))
    st.download_button("Ladda ner PDF", data=pdf_bytes, file_name="självskattning_funktionellt_ledarskap.pdf", mime="application/pdf", type="primary")

    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"
        do_rerun()

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
elif page == "chef_survey":
    render_chef_survey()
elif page == "other_survey":
    render_other_survey()
else:
    render_assessment()
