"""
from reportlab.lib.pagesizes import A4
from datetime import datetime


app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exempel: Ladda ner PDF</title>
<style>
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #f7f7f8; }
.container { max-width: 800px; margin: 4rem auto; background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
h1 { margin-top: 0; }
p { line-height: 1.6; }
.btn { display: inline-block; padding: 0.75rem 1.2rem; border-radius: 10px; text-decoration: none; border: 0; cursor: pointer; font-weight: 600; background: #0d6efd; color: white; }
.btn:hover { filter: brightness(0.95); }
</style>
</head>
<body>
<main class="container">
<h1>Exempelsida</h1>
<p>
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent eget
velit sed nisl auctor consequat. Suspendisse potenti. Nullam facilisis
augue at sapien laoreet, et aliquam eros dictum. Vivamus congue, mi vitae
faucibus mattis, massa nunc aliquet sem, non ultrices nibh neque a augue.
</p>
<a class="btn" href="/ladda-ner">Ladda ner PDF</a>
</main>
</body>
</html>
"""


@app.route("/")
def index():
return render_template_string(INDEX_HTML)


@app.route("/ladda-ner")
def ladda_ner_pdf():
# Generera en enkel PDF i minnet
buffer = io.BytesIO()
pdf = canvas.Canvas(buffer, pagesize=A4)
pdf.setTitle("exempel.pdf")


width, height = A4
margin = 50


pdf.setFont("Helvetica-Bold", 16)
pdf.drawString(margin, height - margin, "Exempel-PDF")


pdf.setFont("Helvetica", 10)
datum = datetime.now().strftime("%Y-%m-%d %H:%M")
pdf.drawString(margin, height - margin - 20, f"Genererad: {datum}")


textobject = pdf.beginText()
textobject.setTextOrigin(margin, height - margin - 60)
textobject.setFont("Helvetica", 12)
lorem = (
"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
"incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
"exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure "
"dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
"Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
"mollit anim id est laborum."
)


# Bryt texten till flera rader
import textwrap
for line in textwrap.wrap(lorem, width=90):
textobject.textLine(line)


pdf.drawText(textobject)
pdf.showPage()
pdf.save()


buffer.seek(0)


return send_file(
buffer,
as_attachment=True,
download_name="exempel.pdf",
mimetype="application/pdf",
)




if __name__ == "__main__":
app.run(debug=True)
