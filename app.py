import io
import os

import requests
from flask import Flask, request, send_file
from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)


@app.route("/")
def upload_file():
    return """
    <!doctype html>
    <title>Upload PDF</title>
    <h1>Upload PDF file</h1>
    <form method="post" action="/process" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload PDF">
    </form>
    <h1>Or enter PDF URL</h1>
    <form method="post" action="/process_url">
      <input type="text" name="url" placeholder="Enter PDF URL">
      <input type="submit" value="Download and Process PDF">
    </form>
    """


@app.route("/process", methods=["POST"])
def process_file():
    file = request.files["file"]
    if file and file.filename.endswith(".pdf"):
        input_path = os.path.join("/tmp", file.filename)
        output_path = os.path.join("/tmp", "output_" + file.filename)
        file.save(input_path)

        # Adjust margins
        add_margin_to_pdf(input_path, output_path, 50, 50)

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

        # Adjust margins
        add_margin_to_pdf(input_path, output_path, 50, 50)

        return send_file(output_path, as_attachment=True)


def add_margin_to_pdf(input_pdf_path, output_pdf_path, right_margin, bottom_margin):
    # Read the existing PDF
    existing_pdf = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in existing_pdf.pages:
        original_width = float(page.MediaBox[2])
        original_height = float(page.MediaBox[3])

        # Create a new PDF with ReportLab
        packet = io.BytesIO()
        new_width = original_width + right_margin
        new_height = original_height + bottom_margin
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
        new_page_merge[-1].x = 0
        new_page_merge[-1].y = bottom_margin
        new_page_merge.render()

        writer.addpage(new_page)

    # Write the output PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)


if __name__ == "__main__":
    app.run(debug=True)
