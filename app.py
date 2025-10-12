def render_id_page():
    st.markdown("## Ange uppgifter för chefens självskattning")
    st.info("Detta steg gäller för Överordnad chef och Medarbetare.")

    base = st.session_state.get("kontakt", {})  # innehåller Funktion m.m.

    with st.form("idform"):
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            chef_first = st.text_input("Chefens förnamn", value=base.get("Chefens förnamn", ""))
            uid = st.text_input("Unikt id", value=base.get("Unikt id", ""))
        with c2:
            st.write("")  # luft
            st.write(f"**Din roll:** {base.get('Funktion','')}")

        ok = st.form_submit_button("Fortsätt", type="primary")

    if ok:
        if not chef_first.strip() or not uid.strip():
            st.warning("Fyll i både **Chefens förnamn** och **Unikt id**.")
            return

        # 1) Logga i SharePoint (via Power Automate) att denna roll gör undersökningen för detta id
        payload_log = {
            "action": "log",
            "uniqueId": uid.strip(),
            "firstName": chef_first.strip(),                # <-- förnamnet med i loggen
            "role": "overchef" if base.get("Funktion") == "Överordnad chef" else "medarbetare",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        ok_log, _, err_log = call_flow(FLOW_LOG_URL, payload_log)
        if not ok_log:
            st.warning(f"Kunde inte logga deltagaren: {err_log}")

        # 2) Hämta namn på chefen från SharePoint via id (så vi kan visa “gäller NN”)
        payload_lookup = {"action": "lookup", "uniqueId": uid.strip()}
        ok_lu, data_lu, err_lu = call_flow(FLOW_LOOKUP_URL, payload_lookup)
        if not ok_lu:
            st.error(f"Kunde inte hämta information för id {uid}: {err_lu}")
            return
        if not data_lu or not data_lu.get("found"):
            st.error(f"Hittade inget objekt i SharePoint för id **{uid}**.")
            return

        # (frivilligt) enkel rimlighetscheck: förnamnet användaren skrev vs. uppslagat namn
        looked_up_name = (data_lu.get("name") or "").strip()
        looked_up_first = looked_up_name.split()[0] if looked_up_name else ""
        if looked_up_first and chef_first.strip().lower() != looked_up_first.lower():
            st.warning(f"Observera: uppgivet förnamn (**{chef_first}**) matchar inte uppslaget namn (**{looked_up_name}**).")

        # Uppdatera kontakt i sessionen (visas låst på resultatsidan och i PDF)
        st.session_state["kontakt"]["Unikt id"] = uid.strip()
        st.session_state["kontakt"]["Chefens förnamn"] = chef_first.strip()
        if data_lu.get("name"):
            st.session_state["kontakt"]["Namn"] = data_lu.get("name")
        if data_lu.get("company"):
            st.session_state["kontakt"]["Företag"] = data_lu.get("company")
        if data_lu.get("email"):
            st.session_state["kontakt"]["E-post"] = data_lu.get("email")

        st.success(f"Undersökningen gäller: **{looked_up_name or chef_first.strip()}**")
        st.session_state["page"] = "assessment"
        do_rerun()

    if st.button("◀ Tillbaka"):
        st.session_state["page"] = "landing"
        do_rerun()
