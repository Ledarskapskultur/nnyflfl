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
