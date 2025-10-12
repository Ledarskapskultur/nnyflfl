from io import BytesIO
from datetime import datetime
import json, textwrap

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
# Innehåll och frågor
# =============================
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "max": 49,
        "text": """I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och lösningarna på verksamhetens utmaningar.

Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.

Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både engagemang, förtroende och delaktighet."""
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "max": 56,
        "text": """Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och förväntade beteenden skapar du trygghet och fokus i arbetet.

Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras, förstärker du önskvärda beteenden och hjälper dina medarbetare att lyckas.

I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser visar ledarskap på riktigt."""
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "max": 35,
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

# =============================
# Hjälpare
# =============================
def do_rerun():
    """Säker rerun som funkar i både nya och äldre Streamlit-versioner."""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()  # fallback

def generate_pdf(title: str, sections, results_map, kontaktinfo: dict) -> bytes:
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
    txt = "   |   ".join(row)
    if len(txt) > 110:
        mid = len(row)//2
        pdf.drawString(margin, y, "   |   ".join(row[:mid])); y -= 14
        pdf.drawString(margin, y, "   |   ".join(row[mid:])); y -= 8
    else:
        pdf.drawString(margin, y, txt); y -= 14

    def ensure(need):
        nonlocal y
        if y - need < 50:
            pdf.showPage()
            pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
            pdf.setFillColor(black); pdf.setFont("Helvetica",9); pdf.drawString(margin, h-40, title)
            y = h - 60

    bg = Color(0.91,0.92,0.94)
    green=Color(0.30,0.69,0.31); orange=Color(0.96,0.65,0.15); blue=Color(0.23,0.51,0.96)

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

        st.session_state["kontakt"] = {
            "Namn": namn.strip(), "Företag": fore.strip(), "Telefon": tel.strip(),
            "E-post": mail.strip(), "Funktion": fun, "Unikt id": ""  # id kan läggas till senare om du vill
        }

        if fun == "Chef":
            # Initiera enkät (inget förifyllt)
            st.session_state["chef_answers"] = [None] * len(QUESTIONS)
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
            do_rerun()
        else:
            st.session_state["page"] = "id_page"
            do_rerun()

def render_id_page():
    st.markdown("## Ange unikt id")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")
    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            uid = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write("")
            st.write(f"**Funktion:** {base.get('Funktion','')}")
        ok = st.form_submit_button("Fortsätt", type="primary")
    if ok:
        if not uid.strip():
            st.warning("Ange ett unikt id.")
            return
        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        st.session_state["page"] = "assessment"
        do_rerun()
    if st.button("◀ Tillbaka"): 
        st.session_state["page"] = "landing"
        do_rerun()

def render_chef_survey():
    st.markdown("## Självskattning (Chef)")
    st.caption("Svara på varje påstående på en skala 1–7 (1 = stämmer inte alls, 7 = stämmer helt).")

    # Scrolla till toppen när flaggan satts
    if st.session_state.get("scroll_to_top"):
        st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)
        st.session_state["scroll_to_top"] = False

    ans = st.session_state.get("chef_answers", [None]*len(QUESTIONS))
    page = st.session_state.get("survey_page", 0)

    per_page = 5
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_slice = list(enumerate(QUESTIONS[start_idx:end_idx], start=start_idx+1))

    for i, q in current_slice:
        st.markdown(f"**{i}. {q}**")

        # Ingen förvald – låt index vara None om ingen valt tidigare
        current_val = ans[i-1]
        idx = None
        if isinstance(current_val, int) and 1 <= current_val <= 7:
            idx = [1,2,3,4,5,6,7].index(current_val)

        selected = st.radio(
            label="",
            options=[1,2,3,4,5,6,7],
            index=idx,
            horizontal=True,
            label_visibility="collapsed",
            key=f"chef_q_{i}",
        )
        # Synka listan med nuvarande state (kommer vara None tills användaren valt)
        st.session_state["chef_answers"][i-1] = st.session_state.get(f"chef_q_{i}")

        if i != current_slice[-1][0]:
            st.divider()

    # Navigering + validering
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if page > 0:
            if st.button("◀ Tillbaka"):
                st.session_state["survey_page"] = page - 1
                st.session_state["scroll_to_top"] = True
                do_rerun()
    with col2:
        page_answers = st.session_state["chef_answers"][start_idx:end_idx]
        all_filled = all(isinstance(v, int) and 1 <= v <= 7 for v in page_answers)

        if page < 3:
            if st.button("Nästa ▶", disabled=not all_filled):
                st.session_state["survey_page"] = page + 1
                st.session_state["scroll_to_top"] = True
                do_rerun()
        else:
            if st.button("Skicka självskattning", type="primary", disabled=not all_filled):
                # Summera resultat för Chef
                a = st.session_state["chef_answers"]
                def ssum(idxs): return sum(a[i] for i in idxs)
                st.session_state["scores"] = {
                    "lyssnande":   {"chef": ssum(IDX_MAP["lyssnande"])},
                    "aterkoppling":{"chef": ssum(IDX_MAP["aterkoppling"])},
                    "malinriktning":{"chef": ssum(IDX_MAP["malinriktning"])},
                }
                st.session_state["page"] = "assessment"
                do_rerun()

def render_assessment():
    st.markdown(f"# {PAGE_TITLE}")

    # Kontaktuppgifter (redigerbara fält)
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

    # Resultatkorten (68/32)
    scores = st.session_state.get("scores", {"lyssnande":{}, "aterkoppling":{}, "malinriktning":{}})
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

    pdf_bytes = generate_pdf(PAGE_TITLE, SECTIONS, scores, st.session_state.get("kontakt", {}))
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
else:
    render_assessment()
