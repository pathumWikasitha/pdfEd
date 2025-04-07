from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from datetime import datetime
from docx.shared import Pt
from docx import Document
import pdfkit

app = Flask(__name__)

# File to store and increment the transaction ID
TRANSACTION_FILE = "transaction_id.json"

# Initialize transaction ID file if not exists
def init_transaction_file():
    if not os.path.exists(TRANSACTION_FILE):
        with open(TRANSACTION_FILE, "w") as f:
            json.dump({"last_id": 494634156}, f)

# Get the next transaction ID
def get_next_transaction_id():
    with open(TRANSACTION_FILE, "r") as f:
        data = json.load(f)

    last_id = data["last_id"]
    next_id = last_id + 13157

    # Save the new ID back
    with open(TRANSACTION_FILE, "w") as f:
        json.dump({"last_id": next_id}, f)

    return str(next_id)

# Replace placeholders in the Word document and change font sizes for specific placeholders
def replace_placeholders(doc_path, output_doc_path, replacements):
    doc = Document(doc_path)

    for p in doc.paragraphs:
        for key, value in replacements.items():
            if key in p.text:
                inline = p.runs
                for run in inline:
                    if key in run.text:
                        run.text = run.text.replace(key, value)
                        # Change font size for specific placeholders
                        if key == "{{PHONE}}":
                            run.font.size = Pt(8.20)  # Set font size to 8 for phone number
                        elif key == "{{DATE}}":
                            run.font.size = Pt(8.20)  # Set font size to 8 for date
                        elif key == "{{TRANSACTION_ID}}":
                            run.font.size = Pt(10.5)  # Set font size to 10.5 for transaction ID

    doc.save(output_doc_path)

# Convert DOCX to PDF
def convert_docx_to_pdf(docx_file, pdf_file):
    pdfkit.from_file(docx_file, pdf_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    user_date = request.form['date']  # Assuming user sends date in YYYY-MM-DD format
    phone_input = request.form['phone']
    
    try:
        date_obj = datetime.strptime(user_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format, please use YYYY-MM-DD."}), 400
    
    # Get current time from system
    current_time = datetime.now().time()
    date_time_input = f"{date_obj} {current_time.strftime('%H:%M:%S')}"

    transaction_id = get_next_transaction_id()
    template_path = "receipt_template.docx"
    modified_docx = f"receipt_{phone_input}.docx"
    output_pdf = f"static/{transaction_id}.pdf"  # Save to static folder

    # Replacements
    replacements = {
        "{{DATE}}": date_time_input,
        "{{PHONE}}": phone_input,
        "{{TRANSACTION_ID}}": transaction_id
    }

    replace_placeholders(template_path, modified_docx, replacements)
    convert_docx_to_pdf(modified_docx, output_pdf)

    if os.path.exists(modified_docx):
        os.remove(modified_docx)

    return jsonify({
        "pdf_url": f"/{output_pdf}",
        "transaction_id": transaction_id
    })

# Serve the generated PDFs
@app.route('/static/<path:filename>')
def download_pdf(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    init_transaction_file()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
