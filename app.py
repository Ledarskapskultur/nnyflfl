def generate_pdf(title: str, sections, results_map):
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Bakgrund
    pdf.setFillColor(HexColor(eggshell_hex))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(black)

    margin_x = 50
    top_y = height - 60
    h1_size = 22
    h2_size = 14
    body_size = 11
    line_h = 16

    # Välj typsnittsnamn
    FN_REG = "OpenSans" if USE_OPEN_SANS else "Helvetica"
    FN_BOLD = "OpenSans-Bold" if USE_OPEN_SANS else "Helvetica-Bold"

    pdf.setTitle("självskattning_funktionellt_ledarskap.pdf")

    # Titel
    pdf.setFont(FN_BOLD, h1_size)
    pdf.drawString(margin_x, top_y, title)

    # Tidsstämpel
    pdf.setFont(FN_REG, 9)
    timestamp = datetime.now().strftime("Genererad: %Y-%m-%d %H:%M")
    pdf.drawRightString(width - margin_x, top_y + 4, timestamp)

    y = top_y - 28

    def ensure_space(needed_px: int):
        nonlocal y
        if y - needed_px < 50:
            pdf.showPage()
            pdf.setFillColor(HexColor(eggshell_hex))
            pdf.rect(0, 0, width, height, fill=1, stroke=0)
            pdf.setFillColor(black)
            pdf.setFont(FN_REG, 9)
            pdf.drawString(margin_x, height - 40, title)
            y = height - 60

    bar_bg = Color(0.91, 0.92, 0.94)
    bar_fg = Color(0.96, 0.65, 0.15)

    for block in sections:
        ensure_space(30)
        pdf.setFont(FN_BOLD, h2_size)
        pdf.drawString(margin_x, y, block["title"])
        y -= h2_size + 6

        pdf.setFont(FN_REG, body_size)
        wrapped = []
        for para in block["text"].split("\n\n"):
            wrapped += textwrap.wrap(para, width=95) + [""]
        for line in wrapped:
            ensure_space(line_h)
            if line:
                pdf.drawString(margin_x, y, line)
            y -= line_h

        score_val = int(results_map.get(block["key"], 0))
        max_val = int(block.get("max", 0))
        ensure_space(36)
        pdf.setFont(FN_BOLD, 10)
        pdf.drawString(margin_x, y, f"Summa {score_val}/{max_val}")
        y -= 12
        bar_w = width - margin_x * 2
        bar_h = 8
        pdf.setFillColor(bar_bg); pdf.rect(margin_x, y, bar_w, bar_h, fill=1, stroke=0)
        fill_w = 0 if max_val == 0 else bar_w * (score_val / max_val)
        pdf.setFillColor(bar_fg); pdf.rect(margin_x, y, fill_w, bar_h, fill=1, stroke=0)
        pdf.setFillColor(black)
        y -= 18

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return buf.getvalue()
