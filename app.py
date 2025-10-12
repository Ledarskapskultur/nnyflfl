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
            "Namn": namn.strip(),
            "Företag": fore.strip(),
            "Telefon": tel.strip(),
            "E-post": mail.strip(),
            "Funktion": fun,
            "Unikt id": generate_unikt_id() if fun == "Chef" else ""
        }

        if fun == "Chef":
            # initiera enkätstate
            st.session_state["chef_answers"] = [None] * len(QUESTIONS)
            st.session_state["survey_page"] = 0
            st.session_state["page"] = "chef_survey"
            st.experimental_rerun()  # ← så att vi hoppar direkt till självskattningen
        else:
            st.session_state["page"] = "id_page"
            st.experimental_rerun()  # ← hoppa direkt till id-sidan
