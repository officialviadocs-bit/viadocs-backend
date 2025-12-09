import os
import zipfile
import io
from flask import Blueprint, request, send_file, jsonify
from pdf2image import convert_from_path

pdf_to_image_bp = Blueprint("pdf_to_image_bp", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-to-image")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"
  # <<< CHANGE THIS PATH


@pdf_to_image_bp.route("/", methods=["POST"])
def pdf_to_image():
    print("USING POPPLER FROM:", POPPLER_PATH)
    try:
        # Check file
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "File must be PDF"}), 400

        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)

        # Convert PDF → images
        images = convert_from_path(pdf_path, dpi=180, poppler_path=POPPLER_PATH)

        # Save images temporarily + zip them
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i, img in enumerate(images, start=1):
                img_filename = f"page_{i}.jpg"
                img_path = os.path.join(UPLOAD_FOLDER, img_filename)
                img.save(img_path, "JPEG")
                zipf.write(img_path, img_filename)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="images.zip"
        )

    except Exception as e:
        print("[PDF2IMAGE] Conversion error:", e)
        return jsonify({"error": str(e)}), 500
