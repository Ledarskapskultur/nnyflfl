from io import BytesIO
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

# ---------- Design (äggskalsvit bakgrund & typografi) ----------
EGGSHELL = "#FAF7F0"  # fast äggskalsvit enligt önskemål
st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {EGGSHELL}; }}
      .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
      html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}

      .stMarkdown h1 {{ font-size: 29px; font-weight: 700; margin: 0 0 6px 0; }}
      .stMarkdown h2 {{ font-size: 19px; font-weight: 700; margin: 24px 0 8px 0; }}
      .stMarkdown p, .stMarkdown {{ font-size: 15px; line-height: 21px; }}

      /* Resultat-kort (som på webben) */
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

      /* Kontaktuppgifter */
      .contact-card {{ background:#fff; border:1px solid rgba(0,0,0,.12); border-radius:12px; padding:12px 14px; box-shadow:0 4px 16px rgba(0,0,0,.06); }}
      .contact-title {{ font-weight:700; font-size:19px; margin: 6px 0 10px 0; }}
      .stTextInput>div>div>input {{ background:#F8FAFC; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Datamodell ----------
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

# Resultat per roll och sektion (dummy – byt mot riktiga värden)
preset_scores = {
    "lyssnande": {"chef": 0, "overchef": 0, "medarbetare": 0},
    "aterkoppling": {"chef": 0, "overchef": 0, "medarbetare": 0},
    "malinriktning": {"chef": 0, "overchef": 0, "medarbetare": 0},
}

ROLE_LABELS = {"chef": "Chef", "overchef": "Överordnad chef", "medarbetare": "Medarbetare"}
ROLE_ORDER = ["chef", "overchef", "medarbetare"]

# ---------- Rendera titel ----------
st.markdown(f"# {PAGE_TITLE}")

# ---------- Kontaktuppgifter ----------
st.markdown("<div class='contact-title'>Kontaktuppgifter</div>", unsafe_allow_html=True)
with st.container():
    st.markdown("<div class='contact-card'>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([0.15, 0.2, 0.2, 0.2, 0.25])
    with c1:
        kontakt_id = st.text_input("Unikt id", value="")
    with c2:
        kontakt_namn = st.text_input("Namn", value="")
    with c3:
        kontakt_foretag = st.text_input("Företag", value="")
    with c4:
        kontakt_tel = st.text_input("Telefon", value="")
    with c5:
        kontakt_epost = st.text_input("E-post", value="")
    st.markdown("</div>", unsafe_allow_html=True)

kontakt = {
    "Unikt id": kontakt_id,
    "Namn": kontakt_namn,
    "Företag": kontakt_foretag,
    "Telefon": kontakt_tel,
    "E-post": kontakt_epost,
}

# ---------- Sektioner 68%/32% + resultatkort ----------
results = {}
for block in SECTIONS:
    left, right = st.columns([0.68, 0.32])
    with left:
        st.header(block["title"])
        for para in block["text"].split("\n\n"):
            st.write(para)
    with right:
        scores = preset_scores.get(block["key"], {r: 0 for r in ROLE_ORDER})
        results[block["key"]] = scores

        st.markdown("<div class='right-wrap'>", unsafe_allow_html=True)
        html = [f"<div class='res-card'>"]

        def bar(lbl, val, maxv, cls):
            pct = 0 if maxv == 0 else val / maxv * 100
            return [
                f"<span class='role-label'>{lbl}: {val} poäng</span>",
                f"<div class='barbg'><span class='barfill {cls}' style='width:{pct:.0f}%'></span></div>",
            ]

        html += bar("Chef", scores.get("chef", 0), block["max"], "bar-green")
        html += bar("Överordnad chef", scores.get("overchef", 0), block["max"], "bar-orange")
        html += bar("Medarbetare", scores.get("medarbetare", 0), block["max"], "bar-blue")
        html += [f"<div class='maxline'>Max: {block['max']} poäng</div>", "</div>"]
        st.markdown("\n".join(html), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Ladda ner PDF som speglar sidan (samma 68/32-linje och färger).")

# ---------- PDF (matchar webben: 68/32 + resultatkort + ingen tidsstämpel) ----------
def build_pdf(title: str, sections, results_map, contact: dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    def bg():
        pdf.setFillColor(HexColor(EGGSHELL))
        pdf.rect(0, 0, w, h, fill=1, stroke=0)
        pdf.setFillColor(black)

    bg()
    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    margin = 50
    y = h - 60

    # H1 (ingen tidsstämpel här)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(margin, y, title)
    y -= 28

    # Kontakt – två rader, i rätt ordning
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
    y -= 6  # liten extra buffert

    def ensure(px: int):
        nonlocal y
        if y - px < 50:
            pdf.showPage()
            bg()
            yy = h - 60
            pdf.setFont("Helvetica-Bold", 22)
            pdf.drawString(margin, yy, title)
            y = yy - 28

    # färger för barer
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
            pdf.showPage(); bg()
            yy = h - 60
            pdf.setFont("Helvetica-Bold", 22); pdf.drawString(margin, yy, title)
            y = yy - 28

        ensure(40)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y, s["title"])
        y -= 20

        section_top = y

        # Höger: resultatkort
        card_pad = 10
        card_w   = right_w - 10
        per_role = 12 + 10 + 14
        card_h   = card_pad + 3*per_role + 10 + card_pad
        card_y   = section_top - card_h + 6

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

    pdf.showPage(); pdf.save(); buf.seek(0); return buf.getvalue()

pdf_bytes = build_pdf(PAGE_TITLE, SECTIONS, preset_scores, kontakt)

st.download_button(
    label="Ladda ner PDF",
    data=pdf_bytes,
    file_name="självskattning_funktionellt_ledarskap.pdf",
    mime="application/pdf",
    type="primary",
)
