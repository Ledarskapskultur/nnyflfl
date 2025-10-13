# app.py – komplett app (svenska)
from __future__ import annotations

from io import BytesIO
from datetime import datetime
import os
import secrets
import string
import textwrap
from typing import List, Tuple

import requests
import streamlit as st
from reportlab.lib.colors import Color, HexColor, black
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ──────────────────────────────────────────────────────────────────────────────
# Grundinställningar & tema
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Självskattning – Funktionellt ledarskap",
                   page_icon="📄", layout="centered")

EGGSHELL = "#FAF7F0"

st.markdown(f"""
<style>
  .stApp {{ background-color:{EGGSHELL}; }}
  .block-container {{ padding-top:2rem; padding-bottom:3rem; }}
  html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
  .stMarkdown h1 {{ font-size:29px; font-weight:700; margin:0 0 6px 0; }}
  .stMarkdown h2 {{ font-size:19px; font-weight:700; margin:24px 0 8px 0; }}
  .stMarkdown p, .stMarkdown {{ font-size:15px; line-height:21px; }}

  .note {{ border-left:6px solid #3B82F6; background:#EAF2FF; color:#0F172A;
           padding:14px 16px; border-radius:10px; }}

  .contact-card {{ background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:12px;
                   padding:12px 14px; box-shadow:0 4px 16px rgba(0,0,0,.06); }}
  .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}

  .right-wrap {{ display:flex; align-items:center; justify-content:center; }}
  .res-card {{ max-width:380px; width:100%; padding:16px 18px; border:1px solid rgba(0,0,0,.12);
               border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.08); background:#fff; }}
  .role-label {{ font-size:13px; color:#111827; margin:10px 0 6px 0; display:block; font-weight:600; }}
  .barbg {{ width:100%; height:10px; background:#E9ECEF; border-radius:6px; overflow:hidden; }}
  .barfill {{ height:10px; display:block; }}
  .bar-green {{ background:#4CAF50; }}
  .bar-orange {{ background:#F5A524; }}
  .bar-blue {{ background:#3B82F6; }}
  .maxline {{ font-size:13px; color:#374151; margin-top:12px; font-weight:600; }}

  /* Viktigt: sänker resultatkortet till brödtextens topp (inte rubriken) */
  .spacer-h2 {{ height: 34px; }}

  /* Hero (rubriken på startsidan) */
  .hero {{ text-align:center; padding:34px 28px; background:#fff; border:1px solid rgba(0,0,0,.12);
           border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,.06); margin-bottom:14px; }}
  .hero h1 {{ font-size:34px; margin:0 0 8px 0; }}
  .hero p  {{ color:#374151; margin:0; }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Power Automate (valfritt – sätt miljövariablerna FLOW_LOOKUP_URL / FLOW_LOG_URL)
# ──────────────────────────────────────────────────────────────────────────────
FLOW_LOOKUP_URL = os.getenv("FLOW_LOOKUP_URL", "").strip()
FLOW_LOG_URL    = os.getenv("FLOW_LOG_URL", "").strip()

def safe_post(url: str, payload: dict) -> Tuple[bool, dict | None, str | None]:
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


# ──────────────────────────────────────────────────────────────────────────────
# Texter, frågor & grupper
# ──────────────────────────────────────────────────────────────────────────────
PAGE_TITLE = "Självskattning – Funktionellt ledarskap"

SECTIONS = [
    {
        "key": "lyssnande",
        "title": "Aktivt lyssnande",
        "max": 49,
        "text": (
            "I dagens arbetsliv har chefens roll förändrats. Medarbetarna sitter ofta på den djupaste kompetensen och "
            "lösningarna på verksamhetens utmaningar.\n\n"
            "Därför är aktivt lyssnande en av chefens viktigaste färdigheter. Det handlar inte bara om att höra vad som "
            "sägs, utan om att förstå, visa intresse och använda den information du får. När du bjuder in till dialog "
            "och tar till dig medarbetarnas perspektiv visar du att deras erfarenheter är värdefulla.\n\n"
            "Genom att agera på det du hör – bekräfta, följa upp och omsätta idéer i handling – stärker du både "
            "engagemang, förtroende och delaktighet."
        ),
    },
    {
        "key": "aterkoppling",
        "title": "Återkoppling",
        "max": 56,
        "text": (
            "Effektiv återkoppling är grunden för både utveckling och motivation. Medarbetare behöver veta vad som "
            "förväntas, hur de ligger till och hur de kan växa. När du som chef tydligt beskriver uppgifter och "
            "förväntade beteenden skapar du trygghet och fokus i arbetet.\n\n"
            "Återkoppling handlar sedan om närvaro och uppföljning – att se, lyssna och ge både beröm och konstruktiv "
            "feedback. Genom att tydligt lyfta fram vad som fungerar och vad som kan förbättras förstärker du "
            "önskvärda beteenden och hjälper dina medarbetare att lyckas.\n\n"
            "I svåra situationer blir återkopplingen extra viktig. Att vara lugn, konsekvent och tydlig när det blåser "
            "visar ledarskap på riktigt."
        ),
    },
    {
        "key": "malinriktning",
        "title": "Målinriktning",
        "max": 35,
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
    },
]

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
EMP_QUESTIONS = CHEF_QUESTIONS
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

IDX_MAP = {"lyssnande": list(range(0, 7)),
           "aterkoppling": list(range(7, 15)),
           "malinriktning": list(range(15, 20))}

INSTR_CHEF = (
    "**Chef**\n\n"
    "Syftet är att du ska beskriva hur du kommunicerar med dina medarbetare i frågor som rör deras arbete.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta **du** gör följande:"
)
INSTR_EMP = (
    "**Medarbetare**\n\n"
    "Syftet är att du ska beskriva hur din chef kommunicerar med dig i frågor som rör ditt arbete.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta **din chef** gör följande:"
)
INSTR_OVER = (
    "**Överordnad chef**\n\n"
    "Syftet är att du ska beskriva hur din underställda chef kommunicerar i arbetsrelaterade frågor.\n\n"
    "Använd följande svarsskala:\n\n"
    "**1 = Aldrig, 2 = Nästan aldrig, 3 = Sällan, 4 = Ibland, 5 = Ofta, 6 = Nästan alltid, 7 = Alltid**.\n\n"
    "Ange hur ofta **din underställda chef** gör följande:"
)

ROLE_LABELS = {"chef": "Chef", "overchef": "Överordnad chef", "medarbetare": "Medarbetare"}
ROLE_ORDER  = ["chef", "overchef", "medarbetare"]


# ──────────────────────────────────────────────────────────────────────────────
# Hjälpfunktioner
# ──────────────────────────────────────────────────────────────────────────────
def generate_unikt_id(n: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def rerun():
    try: st.rerun()
    except AttributeError: st.experimental_rerun()

def sum_by_index(values: List[int | None], idxs: List[int]) -> int:
    return sum(v for i, v in enumerate(values) if i in idxs and isinstance(v, int))

def render_instruction(md: str):
    st.markdown(f"<div class='note'>{md}</div>", unsafe_allow_html=True)
    st.caption("Svara på varje påstående på en skala 1–7. Du måste besvara alla frågor på sidan för att gå vidare.")

def radio_row(key_prefix: str, i: int, current: int | None):
    idx = [1,2,3,4,5,6,7].index(current) if isinstance(current, int) and 1 <= current <= 7 else None
    st.radio("", [1,2,3,4,5,6,7], index=idx, horizontal=True,
             label_visibility="collapsed", key=f"{key_prefix}_{i}")


# ──────────────────────────────────────────────────────────────────────────────
# Sidor
# ──────────────────────────────────────────────────────────────────────────────
def landing():
    # Hero-rubrik (återställd rubrikdel på startsidan)
    st.markdown(
        """
        <div class="hero">
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
            st.warning("Fyll i minst Namn och E-post."); return
        unikt = generate_unikt_id() if fun == "Chef" else ""
        st.session_state["kontakt"] = {"Namn":namn.strip(),"Företag":fore.strip(),"Telefon":tel.strip(),
                                       "E-post":mail.strip(),"Funktion":fun,"Unikt id":unikt}
        if fun == "Chef":
            st.session_state["chef_answers"] = [None]*20
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
        else:
            st.session_state["page"] = "id_page"
        rerun()

def id_page():
    st.markdown("## Ange uppgifter för chefens självskattning")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")
    base = st.session_state.get("kontakt", {})
    with st.form("idform"):
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            first = st.text_input("Chefens förnamn", value=base.get("Chefens förnamn",""))
            uid   = st.text_input("Unikt id", value=base.get("Unikt id",""))
        with c2:
            st.write(""); st.write(f"**Din roll:** {base.get('Funktion','')}")
        ok = st.form_submit_button("Fortsätt", type="primary")

    if ok:
        if not first.strip() or not uid.strip():
            st.warning("Fyll i både **Chefens förnamn** och **Unikt id**."); return
        _ = safe_post(FLOW_LOG_URL, {"action":"log","uniqueId":uid.strip(),"firstName":first.strip(),
                                     "role":"overchef" if base.get("Funktion")=="Överordnad chef" else "medarbetare",
                                     "timestamp": datetime.utcnow().isoformat()+"Z"})
        ok_lu, data_lu, _ = safe_post(FLOW_LOOKUP_URL, {"action":"lookup","uniqueId":uid.strip()})
        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        st.session_state["kontakt"]["Chefens förnamn"] = first.strip()
        if ok_lu and data_lu and data_lu.get("found"):
            for k in ("name","company","email"):
                if data_lu.get(k):
                    st.session_state["kontakt"]["Namn" if k=="name" else ("Företag" if k=="company" else "E-post")] = data_lu[k]
        if base.get("Funktion") == "Medarbetare":
            st.session_state["other_answers"] = [None]*20
            st.session_state["other_page"] = 0
            st.session_state["page"] = "other_survey"
        else:
            st.session_state["over_answers"] = [None]*20
            st.session_state["over_page"] = 0
            st.session_state["page"] = "over_survey"
        rerun()

    if st.button("◀ Tillbaka"): st.session_state["page"]="landing"; rerun()

def survey_core(title: str, instruction: str, questions: List[str], answers_key: str, page_key: str):
    st.markdown(f"## {title}"); render_instruction(instruction)

    if st.session_state.get("scroll_to_top"):
        st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)
        st.session_state["scroll_to_top"] = False

    ans = st.session_state.get(answers_key, [None]*20)
    page = st.session_state.get(page_key, 0)

    per = 5; start, end = page*per, page*per+per
    for i, q in enumerate(questions[start:end], start=start+1):
        st.markdown(f"**{i}. {q}**"); radio_row(answers_key, i, ans[i-1])
        st.session_state[answers_key][i-1] = st.session_state.get(f"{answers_key}_{i}")
        if i < end: st.divider()

    left, right = st.columns([0.5, 0.5])
    with left:
        if page > 0 and st.button("◀ Tillbaka"):
            st.session_state[page_key] = page - 1; st.session_state["scroll_to_top"] = True; rerun()
    with right:
        ok_page = all(isinstance(v,int) and 1<=v<=7 for v in st.session_state[answers_key][start:end])
        if page < 3:
            if st.button("Nästa ▶", disabled=not ok_page):
                st.session_state[page_key] = page + 1; st.session_state["scroll_to_top"] = True; rerun()
        else:
            if st.button("Skicka självskattning", type="primary", disabled=not ok_page):
                st.session_state["page"] = "assessment"; rerun()

def chef_survey():  survey_core("Självskattning (Chef)", INSTR_CHEF, CHEF_QUESTIONS, "chef_answers", "survey_page")
def other_survey(): survey_core("Självskattning (Medarbetare)", INSTR_EMP, EMP_QUESTIONS, "other_answers", "other_page")
def over_survey():  survey_core("Självskattning (Överordnad chef)", INSTR_OVER, OVER_QUESTIONS, "over_answers", "over_page")


# ──────────────────────────────────────────────────────────────────────────────
# Resultat
# ──────────────────────────────────────────────────────────────────────────────
def assessment():
    # summera
    scores = st.session_state.get("scores", {"lyssnande":{}, "aterkoppling":{}, "malinriktning":{}})
    if "chef_answers"  in st.session_state:
        a = st.session_state["chef_answers"]
        scores["lyssnande"]["chef"]     = sum_by_index(a, IDX_MAP["lyssnande"])
        scores["aterkoppling"]["chef"]  = sum_by_index(a, IDX_MAP["aterkoppling"])
        scores["malinriktning"]["chef"] = sum_by_index(a, IDX_MAP["malinriktning"])
    if "other_answers" in st.session_state:
        a = st.session_state["other_answers"]
        scores["lyssnande"]["medarbetare"]     = sum_by_index(a, IDX_MAP["lyssnande"])
        scores["aterkoppling"]["medarbetare"]  = sum_by_index(a, IDX_MAP["aterkoppling"])
        scores["malinriktning"]["medarbetare"] = sum_by_index(a, IDX_MAP["malinriktning"])
    if "over_answers"  in st.session_state:
        a = st.session_state["over_answers"]
        scores["lyssnande"]["overchef"]     = sum_by_index(a, IDX_MAP["lyssnande"])
        scores["aterkoppling"]["overchef"]  = sum_by_index(a, IDX_MAP["aterkoppling"])
        scores["malinriktning"]["overchef"] = sum_by_index(a, IDX_MAP["malinriktning"])
    st.session_state["scores"] = scores

    st.markdown(f"# {PAGE_TITLE}")

    # Kontakt (låsta fält)
    st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='contact-card'>", unsafe_allow_html=True)
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

    # Sektioner – 68/32 + resultatkort linjerat med brödtext
    for s in SECTIONS:
        left, right = st.columns([0.68, 0.32])
        with left:
            st.header(s["title"])
            for p in s["text"].split("\n\n"):
                st.write(p)
        with right:
            st.markdown("<div class='spacer-h2'></div>", unsafe_allow_html=True)
            key, mx = s["key"], s["max"]
            chef = int(scores.get(key,{}).get("chef",0))
            over = int(scores.get(key,{}).get("overchef",0))
            med  = int(scores.get(key,{}).get("medarbetare",0))

            st.markdown("<div class='right-wrap'>", unsafe_allow_html=True)
            html = ["<div class='res-card'>"]
            def bar(lbl, val, maxv, cls):
                pct = 0 if maxv==0 else val/maxv*100
                return [
                    f"<span class='role-label'>{lbl}: {val} poäng</span>",
                    f"<div class='barbg'><span class='barfill {cls}' style='width:{pct:.0f}%'></span></div>",
                ]
            html += bar("Chef", chef, mx, "bar-green")
            html += bar("Överordnad chef", over, mx, "bar-orange")
            html += bar("Medarbetare", med, mx, "bar-blue")
            html += [f"<div class='maxline'>Max: {mx} poäng</div>", "</div>"]
            st.markdown("\n".join(html), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.caption("Ladda ner PDF som speglar sidan (samma 68/32-linje).")
    pdf = build_pdf(PAGE_TITLE, SECTIONS, scores, st.session_state.get("kontakt", {}))
    k = st.session_state.get("kontakt", {})
    pdf_name = f"Självskattning - {k.get('Namn') or 'Person'} - {k.get('Företag') or 'Företag'}.pdf"
    st.download_button("Ladda ner PDF", data=pdf, file_name=pdf_name,
                       mime="application/pdf", type="primary")

    if st.button("◀ Till startsidan"):
        st.session_state["page"] = "landing"; rerun()


# ──────────────────────────────────────────────────────────────────────────────
# PDF – två kolumner 68/32, staplar i linje med brödtext
# ──────────────────────────────────────────────────────────────────────────────
def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
    pdf.setFillColor(black)
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    margin = 50; y = h - 60
    pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, y, title)
    pdf.setFont("Helvetica", 9); pdf.drawRightString(w - margin, y+4, datetime.now().strftime("Genererad: %Y-%m-%d %H:%M"))
    y -= 28

    # Kontakt
    pdf.setFont("Helvetica-Bold", 10); pdf.drawString(margin, y, "Kontaktuppgifter"); y -= 14
    pdf.setFont("Helvetica", 10)
    row = [
        f"Unikt id: {contact.get('Unikt id','')}",
        f"Namn: {contact.get('Namn','')}",
        f"Företag: {contact.get('Företag','')}",
        f"Telefon: {contact.get('Telefon','')}",
        f"E-post: {contact.get('E-post','')}",
    ]
    line = "   |   ".join(row)
    if len(line) > 110:
        mid = len(row)//2
        pdf.drawString(margin, y, "   |   ".join(row[:mid])); y -= 14
        pdf.drawString(margin, y, "   |   ".join(row[mid:])); y -= 8
    else:
        pdf.drawString(margin, y, line); y -= 14

    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage(); pdf.setFillColor(HexColor(EGGSHELL)); pdf.rect(0,0,w,h,fill=1,stroke=0)
            pdf.setFillColor(black); pdf.setFont("Helvetica",9); pdf.drawString(margin, h-40, title); y = h - 60

    bar_bg = Color(0.91,0.92,0.94); green=Color(0.30,0.69,0.31); orange=Color(0.96,0.65,0.15); blue=Color(0.23,0.51,0.96)

    # två kolumner 68/32
    content_w = w - 2*margin
    left_w = content_w * 0.68
    right_w = content_w - left_w

    for s in sections:
        ensure(30)
        pdf.setFont("Helvetica-Bold", 14); pdf.drawString(margin, y, s["title"]); y -= 20

        y_top = y  # samma start för båda kolumner

        # Höger: staplar i linje med brödtext
        y_right = y_top
        pdf.setFont("Helvetica", 10)
        for role, col in [("chef", green), ("overchef", orange), ("medarbetare", blue)]:
            val = int(results_map.get(s["key"], {}).get(role, 0))
            mx  = int(s["max"])
            pdf.drawString(margin + left_w + 10, y_right, f"{ROLE_LABELS[role]} – Summa {val}/{mx}")
            y_right -= 12
            pdf.setFillColor(bar_bg); pdf.rect(margin + left_w + 10, y_right, right_w - 20, 8, fill=1, stroke=0)
            fw = 0 if mx==0 else (right_w - 20) * (val/mx)
            pdf.setFillColor(col); pdf.rect(margin + left_w + 10, y_right, fw, 8, fill=1, stroke=0)
            pdf.setFillColor(black); y_right -= 14

        # Vänster: brödtext inom left_w
        pdf.setFont("Helvetica", 11)
        y_left = y_top
        approx_chars = max(40, int(95 * (left_w / content_w)))  # enkel approx för wrap
        for para in s["text"].split("\n\n"):
            for ln in textwrap.wrap(para, width=approx_chars):
                ensure(16); pdf.drawString(margin, y_left, ln); y_left -= 16
            y_left -= 4

        y = min(y_left, y_right) - 12  # nästa sektion under lägsta punkt

    pdf.showPage(); pdf.save(); buf.seek(0); return buf.getvalue()


# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────
st.session_state.setdefault("page", "landing")

ROUTES = {
    "landing": landing,
    "id_page": id_page,
    "chef_survey": chef_survey,
    "other_survey": other_survey,
    "over_survey": over_survey,
    "assessment": assessment,
}
ROUTES[st.session_state["page"]]()
