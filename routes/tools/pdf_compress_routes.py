import os
import subprocess
from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

# ===========================================
#  PDF Compressor Blueprint
# ===========================================
pdf_compress_bp = Blueprint("pdf_compress_bp", __name__)

# Folder to store temporary files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-compress")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@pdf_compress_bp.route("", methods=["POST", "OPTIONS"])
@jwt_required(optional=True)
def compress_pdf():
    """
    Compress a PDF using Ghostscript.
    Accepts:
    - file (PDF)
    - mode (extreme, recommended, low)
    """

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS Preflight OK"}), 200

    try:
        # --------------------------
        # Validate file input
        # --------------------------
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        filename = secure_filename(file.filename)

        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400

        # Save uploaded PDF
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        # --------------------------
        # Select compression mode
        # --------------------------
        mode = request.form.get("mode", "recommended").lower()
        settings_map = {
            "extreme": "/screen",      # lowest quality → smallest file
            "recommended": "/ebook",   # good quality → recommended
            "low": "/printer"          # high quality → least compression
        }
        pdf_setting = settings_map.get(mode, "/ebook")

        # Output file path
        output_filename = f"compressed_{filename}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        # --------------------------
        # Ghostscript Executable
        # --------------------------

        # Correct fixed path for Windows
        if os.name == "nt":
            gs_executable = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"
        else:
            gs_executable = "gs"

        print("USING GHOSTSCRIPT:", gs_executable)

        # Ghostscript command
        gs_command = [
            gs_executable,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={pdf_setting}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]

        # --------------------------
        # Run Ghostscript
        # --------------------------
        subprocess.run(gs_command, check=True)

        # --------------------------
        # File size calculation
        # --------------------------
        original_size = os.path.getsize(input_path) / (1024 * 1024)
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)

        print(f"✅ Compression success: {original_size:.2f}MB → {compressed_size:.2f}MB")

        # --------------------------
        # Send compressed file
        # --------------------------
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf",
        )

        response.headers["x-original-size-mb"] = f"{original_size:.2f}"
        response.headers["x-compressed-size-mb"] = f"{compressed_size:.2f}"

        return response

    except subprocess.CalledProcessError as e:
        print("❌ Ghostscript compression failed:", str(e))
        return jsonify({
            "error": "Ghostscript failed. Make sure Ghostscript is installed correctly.",
            "details": str(e)
        }), 500

    except Exception as e:
        print("❌ Server Error:", str(e))
        return jsonify({"error": f"Server error: {str(e)}"}), 500
