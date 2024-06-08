import io
import os

import requests
from flask import Flask, render_template, request, send_file
from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.pdfgen import canvas

app = Flask(__name__)


@app.route("/")
def upload_file():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process_file():
    file = request.files["file"]
    if file and file.filename.endswith(".pdf"):
        input_path = os.path.join("/tmp", file.filename)
        output_path = os.path.join("/tmp", "output_" + file.filename)
        file.save(input_path)

        # Get margins from form
        margin_top = int(request.form["margin_top"])
        margin_bottom = int(request.form["margin_bottom"])
        margin_left = int(request.form["margin_left"])
        margin_right = int(request.form["margin_right"])

        # Adjust margins
        add_margin_to_pdf(
            input_path,
            output_path,
            margin_top,
            margin_bottom,
            margin_left,
            margin_right,
        )

        return send_file(output_path, as_attachment=True)


@app.route("/process_url", methods=["POST"])
def process_url():
    pdf_url = request.form["url"]
    if pdf_url:
        response = requests.get(pdf_url)
        input_path = "/tmp/input.pdf"
        output_path = "/tmp/output.pdf"

        with open(input_path, "wb") as f:
            f.write(response.content)

        # Get margins from form
        margin_top = int(request.form["margin_top"])
        margin_bottom = int(request.form["margin_bottom"])
        margin_left = int(request.form["margin_left"])
        margin_right = int(request.form["margin_right"])

        # Adjust margins
        add_margin_to_pdf(
            input_path,
            output_path,
            margin_top,
            margin_bottom,
            margin_left,
            margin_right,
        )

        return send_file(output_path, as_attachment=True)


def add_margin_to_pdf(
    input_pdf_path,
    output_pdf_path,
    margin_top,
    margin_bottom,
    margin_left,
    margin_right,
):
    # Read the existing PDF
    existing_pdf = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in existing_pdf.pages:
        original_width = float(page.MediaBox[2])
        original_height = float(page.MediaBox[3])

        # Create a new PDF with ReportLab
        packet = io.BytesIO()
        new_width = original_width + margin_left + margin_right
        new_height = original_height + margin_top + margin_bottom
        can = canvas.Canvas(packet, pagesize=(new_width, new_height))
        can.showPage()
        can.save()

        # Move to the beginning of the StringIO buffer
        packet.seek(0)

        # Read the new PDF with margins
        new_pdf = PdfReader(packet)
        new_page = new_pdf.pages[0]

        # Merge the original page onto the new page with margins
        new_page_merge = PageMerge(new_page)
        new_page_merge.add(page).render()

        # Adjust the original page position
        new_page_merge[-1].x = margin_left
        new_page_merge[-1].y = margin_bottom
        new_page_merge.render()

        writer.addpage(new_page)

    # Write the output PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    app.run(debug=True)
