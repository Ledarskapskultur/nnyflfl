from io import BytesIO
from datetime import datetime
import os, json, secrets, string, textwrap, requests

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, Color

# =============================
# Konfiguration
# =============================
EGGSHELL = "#FAF7F0"
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

# Skicka summerna till Power Automate när CHEF skickar in enkäten
SEND_TO_FLOW_AFTER_SURVEY = True

# Din Flow-URL (kan överskridas via env FLOW_URL)
FLOW_URL_DEFAULT = (
    "https://default1ad3791223f4412ea6272223201343.20.environment.api.powerplatform.com:443/"
    "powerautomate/automations/direct/workflows/bff5923897b04a39bc6ba69ea4afde69/triggers/manual/"
    "paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=B1rjO0FhY0ZxXO8VJvWPmcLAv-LMCgICG6tDguPmhwQ"
)
FLOW_URL = os.getenv("FLOW_URL", FLOW_URL_DEFAULT).strip()

# =============================
# Tema / CSS
# =============================
st.set_page_config(page_title=PAGE_TITLE, page_icon="📄", layout="centered")
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
      .ok-badge {{ color:#065f46; background:#d1fae5; padding:2px 8px; border-radius:9999px; font-size:12px; }}
      .err-badge {{ color:#991b1b; background:#fee2e2; padding:2px 8px; border-radius:9999px; font-size:12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Texter & sektioner
# =============================
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

# 20 frågor, exakt ordning, Likert 1–7
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

ROLE_LABELS = {"chef": "Chef", "overchef": "Överordnad chef", "medarbetare": "Medarbetare"}
ROLE_ORDER = ["chef", "overchef", "medarbetare"]

# =============================
# Hjälpfunktioner
# =============================
def generate_unikt_id(n=8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def send_to_flow(payload: dict) -> tuple[bool, str | None, str | None]:
    """POST till Power Automate. Returnerar (ok, ev_returnerat_id, fel)."""
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

def pdf_from_page(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
    pdf.setFillColor(black)

    margin = 50
    y = h - 60
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")
    pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, y, title)
    pdf.setFont("Helvetica", 9); pdf.drawRightString(w - margin, y+4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
    y -= 28

    # Kontakt
    pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    parts = [
        f"Unikt id: {kontaktinfo.get('Unikt id','')}",
        f"Namn: {kontaktinfo.get('Namn','')}",
        f"Företag: {kontaktinfo.get('Företag','')}",
        f"Telefon: {kontaktinfo.get('Telefon','')}",
        f"E-post: {kontaktinfo.get('E-post','')}",
        f"Funktion: {kontaktinfo.get('Funktion','')}",
    ]
    line = "   |   ".join(parts)
    if len(line) > 110:
        mid = len(parts)//2
        pdf.drawString(margin, y, "   |   ".join(parts[:mid])); y -= 14
        pdf.drawString(margin, y, "   |   ".join(parts[mid:])); y -= 8
    else:
        pdf.drawString(margin, y, line); y -= 14

    def ensure(need):
        nonlocal y
        if y - need < 50:
            pdf.showPage(); pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
            pdf.setFillColor(black); pdf.setFont("Helvetica",9); pdf.drawString(margin, h-40, title); y = h - 60

    bg = Color(0.91,0.92,0.94)
    green = Color(0.30,0.69,0.31)
    orange = Color(0.96,0.65,0.15)
    blue = Color(0.23,0.51,0.96)

    for s in sections:
        ensure(30)
        pdf.setFont("Helvetica-Bold", 14); pdf.drawString(margin, y, s["title"]); y -= 20
        pdf.setFont("Helvetica", 11)
        for para in s["text"].split("\n\n"):
            for ln in textwrap.wrap(para, width=95):
                ensure(16); pdf.drawString(margin, y, ln); y -= 16

        def draw(label, val, maxv, col):
            nonlocal y
            ensure(26); pdf.setFont("Helvetica-Bold",10); pdf.drawString(margin, y, f"{label}: {val} poäng"); y -= 12
            bw, bh = w-2*margin, 8; pdf.setFillColor(bg); pdf.rect(margin, y, bw, bh, fill=1, stroke=0)
            fw = 0 if maxv==0 else bw*(val/maxv); pdf.setFillColor(col); pdf.rect(margin, y, fw, bh, fill=1, stroke=0)
            pdf.setFillColor(black); y -= 14

        key = s["key"]; mx = s["max"]
        draw("Chef",            int(results_map.get(key,{}).get("chef",0)),        mx, green)
        draw("Överordnad chef", int(results_map.get(key,{}).get("overchef",0)),    mx, orange)
        draw("Medarbetare",     int(results_map.get(key,{}).get("medarbetare",0)), mx, blue)
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
        st.session_state["kontakt"] = {
            "Namn": namn.strip(), "Företag": fore.strip(), "Telefon": tel.strip(),
            "E-post": mail.strip(), "Funktion": fun,
            "Unikt id": generate_unikt_id() if fun=="Chef" else ""
        }
        st.session_state["page"] = "chef_survey" if fun == "Chef" else "id_page"

def render_id_page():
    st.markdown("## Ange unikt id")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")
    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            uid = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write(""); st.write(f"**Funktion:** {base.get('Funktion','')}")
        ok = st.form_submit_button("Fortsätt", type="primary")
    if ok:
        if not uid.strip():
            st.warning("Ange ett unikt id.")
            return
        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        st.session_state["page"] = "assessment"
    if st.button("◀ Tillbaka"):
        st.session_state["page"] = "landing"

def render_chef_survey():
    st.markdown("## Självskattning (Chef)")
    st.caption("Svara på varje påstående på en skala 1–7 (1 = stämmer inte alls, 7 = stämmer helt).")

    # init
    if "chef_answers" not in st.session_state:
        st.session_state["chef_answers"] = [0] * len(QUESTIONS)

    ans = st.session_state["chef_answers"]

    for i, q in enumerate(QUESTIONS, start=1):
        st.markdown(f"**{i}. {q}**")
        default_idx = (ans[i-1] - 1) if 1 <= ans[i-1] <= 7 else 3
        ans[i-1] = st.radio(
            label="",
            options=[1, 2, 3, 4, 5, 6, 7],
            index=default_idx,
            horizontal=True,
            label_visibility="collapsed",
            help=None,
            key=f"chef_q_{i}",
        )
        if i < len(QUESTIONS):
            st.divider()

    if st.button("Skicka självskattning", type="primary"):
        # summera
        def ssum(idxs): return sum(ans[i] for i in idxs)
        sums = {
            "lyssnande":   ssum(IDX_MAP["lyssnande"]),
            "aterkoppling":ssum(IDX_MAP["aterkoppling"]),
            "malinriktning":ssum(IDX_MAP["malinriktning"]),
        }
        # spara i session
        st.session_state["scores"] = {
            "lyssnande":   {"chef": int(sums["lyssnande"])},
            "aterkoppling":{"chef": int(sums["aterkoppling"])},
            "malinriktning":{"chef": int(sums["malinriktning"])},
        }

        # (valfritt) skicka till Flow (schema med secret = unikt id)
        if SEND_TO_FLOW_AFTER_SURVEY:
            kontakt = st.session_state.get("kontakt", {})
            payload = {
                "title": PAGE_TITLE,
                "name": kontakt.get("Namn",""),
                "company": kontakt.get("Företag",""),
                "email": kontakt.get("E-post",""),
                "sumListening": int(sums["lyssnande"]),
                "sumFeedback":  int(sums["aterkoppling"]),
                "sumGoal":      int(sums["malinriktning"]),
                "answersJson":  json.dumps(
                    [{"nr":i+1,"question":QUESTIONS[i],"answer":ans[i]} for i in range(len(QUESTIONS))],
                    ensure_ascii=False
                ),
                "submittedAt":  datetime.utcnow().isoformat() + "Z",
                "secret":       kontakt.get("Unikt id",""),  # <-- unika id:t skickas här
                "hasPdf":       False,
                "pdfBase64":    "",
                "fileName":     "",
            }
            ok, ret_uid, err = send_to_flow(payload)
            if ok and ret_uid:
                st.session_state["kontakt"]["Unikt id"] = ret_uid
                st.success(f"Skickat. Unikt id: {ret_uid}")
            elif ok:
                st.success("Skickat till Power Automate.")
            else:
                st.error(f"Kunde inte skicka till Power Automate: {err}")

        st.session_state["page"] = "assessment"

def render_assessment():
    st.markdown(f"# {PAGE_TITLE}")

    # Kontaktkort
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card contact-card'>", unsafe_allow_html=True)
        base = st.session_state.get("kontakt", {"Namn":"","Företag":"","Telefon":"","E-post":"","Funktion":"Chef","Unikt id":""})
        c1, c2, c3 = st.columns([0.4, 0.3, 0.3])
        with c1:
            n = st.text_input("Namn", value=base.get("Namn",""))
            e = st.text_input("E-post", value=base.get("E-post",""))
        with c2:
            f = st.text_input("Företag", value=base.get("Företag",""))
            t = st.text_input("Telefon", value=base.get("Telefon",""))
        with c3:
            fun = st.selectbox("Funktion", ["Chef","Överordnad chef","Medarbetare"],
                               index=["Chef","Överordnad chef","Medarbetare"].index(base.get("Funktion","Chef")))
            uid = st.text_input("Unikt id", value=base.get("Unikt id",""))
        st.session_state["kontakt"] = {"Namn":n,"E-post":e,"Företag":f,"Telefon":t,"Funktion":fun,"Unikt id":uid}
        st.markdown("</div>", unsafe_allow_html=True)

    # Resultat (68/32)
    scores = st.session_state.get("scores", {"lyssnande":{}, "aterkoppling":{}, "malinriktning":{}})
    for s in SECTIONS:
        left, right = st.columns([0.68, 0.32])
        with left:
            st.header(s["title"])
            for para in s["text"].split("\n\n"):
                st.write(para)
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
    st.caption("Ladda ner PDF som speglar innehållet.")

    pdf_bytes = pdf_from_page(PAGE_TITLE, SECTIONS, scores, st.session_state.get("kontakt", {}))
    st.download_button(
        "Ladda ner PDF",
        data=pdf_bytes,
        file_name="självskattning_funktionellt_ledarskap.pdf",
        mime="application/pdf",
        type="primary",
    )

    if st.button("◀ Till startsidan"):
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
elif page == "chef_survey":
    render_chef_survey()
else:
    render_assessment()
