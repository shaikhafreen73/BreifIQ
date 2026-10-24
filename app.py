import os
import json
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, abort
)
from werkzeug.utils import secure_filename

# Local Modules
from db import (
    init_db, create_user, authenticate_user, get_user_by_id,
    update_user_profile, save_analysis, get_history_by_id,
    get_user_history, get_user_stats, delete_history_item
)
from document_processor import is_tabular_file, process_document
from excel_reader import read_file
from data_analyzer import analyze_dataset
from summarizer import analyze_document_text
from report_generator import generate_pdf_report
from chat_engine import answer_question

app = Flask(__name__, template_folder="Templates", static_folder="Static")
app.secret_key = os.environ.get("SECRET_KEY", "briefiq-capstone-deeplearning-2026-secret-key")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "Uploads")
REPORT_FOLDER = os.path.join(os.path.dirname(__file__), "Reports")
SAMPLE_FOLDER = os.path.join(os.path.dirname(__file__), "samples")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# Initialize database tables
init_db()


# Context Processor to make current_user available in all Jinja templates
@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
    return dict(current_user=user)


# ==========================================================
# AUTHENTICATION ROUTES
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        if not identifier or not password:
            flash("Please enter both username/email and password.", "error")
            return render_template("login.html")

        user = authenticate_user(identifier, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please verify your login details.", "error")

    return render_template("login.html")


@app.route("/demo-login", methods=["POST"])
def demo_login():
    """One-click instant demo login for evaluators and guests."""
    user = authenticate_user("demo_user", "demo123")
    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]
        flash("Logged in as Demo Researcher! You can now analyze documents and view history.", "success")
    else:
        flash("Could not initialize demo session.", "error")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "Student").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not full_name or not username or not email or not password:
            flash("All fields marked with * are required.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match. Please retype carefully.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")

        result = create_user(username, email, password, full_name, role)
        if result["success"]:
            session["user_id"] = result["user_id"]
            session["username"] = username
            session["full_name"] = full_name
            session["role"] = role
            flash("Account registered successfully! Welcome to BriefIQ.", "success")
            return redirect(url_for("home"))
        else:
            flash(result["error"], "error")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been securely signed out. See you soon!", "info")
    return redirect(url_for("login"))


# ==========================================================
# MAIN APPLICATION ROUTES
# ==========================================================

@app.route("/")
def home():
    user_id = session.get("user_id")
    recent_history = get_user_history(user_id, limit=4)
    stats = get_user_stats(user_id)
    return render_template("index.html", recent_history=recent_history, stats=stats)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your personal profile and analysis history.", "info")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "Student").strip()
        if full_name:
            update_user_profile(user_id, full_name, role)
            session["full_name"] = full_name
            session["role"] = role
            flash("Your profile information has been successfully updated.", "success")

    user = get_user_by_id(user_id)
    history = get_user_history(user_id, limit=50)
    stats = get_user_stats(user_id)

    return render_template("profile.html", user=user, history=history, stats=stats)


# ==========================================================
# DOCUMENT UPLOAD & PROCESSING
# ==========================================================

@app.route("/upload", methods=["POST"])
def upload():
    if "document" not in request.files:
        flash("No file was selected in the form submission.", "error")
        return redirect(url_for("home"))

    file = request.files["document"]

    if file.filename == "":
        flash("Please select a document or dataset file to analyze.", "error")
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)
    if not filename:
        filename = "uploaded_document"

    filepath = os.path.join(app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER), filename)
    file.save(filepath)

    file_size_kb = round(os.path.getsize(filepath) / 1024, 1)
    summary_mode = request.form.get("summary_mode", "detailed")
    user_id = session.get("user_id")

    try:
        # Check if file is tabular dataset
        if is_tabular_file(filename):
            data = read_file(filepath)
            analysis = analyze_dataset(data)

            history_id = save_analysis(
                user_id=user_id,
                filename=filename,
                file_type=os.path.splitext(filename)[1].upper().replace(".", ""),
                file_size_kb=file_size_kb,
                analysis_type="dataset",
                summary_title=f"Dataset Report: {filename}",
                summary_content=analysis["ai_summary"],
                kpis=analysis["kpis"],
                chart_data=analysis["chart_data"],
                table_data={
                    "columns": analysis["columns"],
                    "rows": analysis["rows"][:50]  # Store top 50 rows for display
                },
                individual_summaries=analysis["individual_summaries"]
            )

            flash("Dataset parsed and analytical report generated successfully!", "success")
            return redirect(url_for("result_view", history_id=history_id))

        else:
            # Universal document processing (PDF, DOCX, TXT, MD, etc.)
            doc_data = process_document(filepath)
            text = doc_data["text"]

            if not text or len(text.strip()) == 0:
                flash(f"No readable text could be extracted from '{filename}'. Please ensure the document is not an image scan.", "error")
                return redirect(url_for("home"))

            summary_res = analyze_document_text(text, summary_mode=summary_mode)

            history_id = save_analysis(
                user_id=user_id,
                filename=filename,
                file_type=doc_data["file_type"],
                file_size_kb=file_size_kb,
                analysis_type="summary",
                summary_title=f"AI Summary: {doc_data['title']}",
                summary_content=summary_res["summary"],
                kpis=summary_res["metrics"],
                chart_data={
                    "takeaways": summary_res["takeaways"],
                    "page_count": doc_data["page_count"]
                },
                table_data=None,
                individual_summaries=None
            )

            flash("Deep learning summary generated successfully with T5-small!", "success")
            return redirect(url_for("result_view", history_id=history_id))

    except Exception as e:
        flash(f"Error processing file '{filename}': {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/sample/<sample_type>", methods=["GET", "POST"])
def try_sample(sample_type):
    """Loads a pre-generated sample file for immediate 1-click testing."""
    sample_mapping = {
        "pdf": ("sample_ai_research.pdf", False),
        "csv": ("sample_student_grades.csv", True),
        "excel": ("sample_sales_analytics.xlsx", True),
        "docx": ("sample_executive_brief.docx", False)
    }

    if sample_type not in sample_mapping:
        flash("Invalid sample selection.", "error")
        return redirect(url_for("home"))

    filename, is_tabular = sample_mapping[sample_type]
    filepath = os.path.join(SAMPLE_FOLDER, filename)

    if not os.path.exists(filepath):
        from create_samples import create_sample_pdf, create_sample_csv, create_sample_excel, create_sample_docx
        create_sample_pdf()
        create_sample_csv()
        create_sample_excel()
        create_sample_docx()

    file_size_kb = round(os.path.getsize(filepath) / 1024, 1)
    user_id = session.get("user_id")

    try:
        if is_tabular:
            df = read_file(filepath)
            analysis = analyze_dataset(df)
            history_id = save_analysis(
                user_id=user_id,
                filename=filename,
                file_type=os.path.splitext(filename)[1].upper().replace(".", ""),
                file_size_kb=file_size_kb,
                analysis_type="dataset",
                summary_title=f"Sample Dataset: {filename}",
                summary_content=analysis["ai_summary"],
                kpis=analysis["kpis"],
                chart_data=analysis["chart_data"],
                table_data={
                    "columns": analysis["columns"],
                    "rows": analysis["rows"]
                },
                individual_summaries=analysis["individual_summaries"]
            )
            flash(f"Sample dataset '{filename}' loaded successfully!", "success")
            return redirect(url_for("result_view", history_id=history_id))
        else:
            doc_data = process_document(filepath)
            summary_res = analyze_document_text(doc_data["text"], summary_mode="detailed")
            history_id = save_analysis(
                user_id=user_id,
                filename=filename,
                file_type=doc_data["file_type"],
                file_size_kb=file_size_kb,
                analysis_type="summary",
                summary_title=f"Sample Document: {filename}",
                summary_content=summary_res["summary"],
                kpis=summary_res["metrics"],
                chart_data={
                    "takeaways": summary_res["takeaways"],
                    "page_count": doc_data["page_count"]
                },
                table_data=None,
                individual_summaries=None
            )
            flash(f"Sample document '{filename}' analyzed with T5-small successfully!", "success")
            return redirect(url_for("result_view", history_id=history_id))
    except Exception as e:
        flash(f"Failed to load sample: {str(e)}", "error")
        return redirect(url_for("home"))


# ==========================================================
# RESULT AND EXPORT ROUTES
# ==========================================================

@app.route("/result/<int:history_id>")
def result_view(history_id):
    analysis = get_history_by_id(history_id)
    if not analysis:
        flash("Analysis record not found.", "error")
        return redirect(url_for("home"))

    is_table = (analysis.get("analysis_type") == "dataset")
    takeaways = []
    if not is_table and analysis.get("chart_data"):
        takeaways = analysis["chart_data"].get("takeaways", [])

    return render_template(
        "result.html",
        analysis=analysis,
        is_table=is_table,
        takeaways=takeaways,
        ai_summary=analysis.get("summary_content", ""),
        kpis=analysis.get("kpis") or {},
        chart_data=analysis.get("chart_data") or {},
        columns=analysis.get("table_data", {}).get("columns", []) if analysis.get("table_data") else [],
        rows=analysis.get("table_data", {}).get("rows", []) if analysis.get("table_data") else [],
        individual_summaries=analysis.get("individual_summaries") or []
    )


@app.route("/result")
def result_legacy():
    """Fallback route for any direct GET to /result without id."""
    user_id = session.get("user_id")
    recent = get_user_history(user_id, limit=1)
    if recent:
        return redirect(url_for("result_view", history_id=recent[0]["id"]))
    flash("No recent document analysis found. Please upload a file to begin.", "info")
    return redirect(url_for("home"))


@app.route("/download-report/<int:history_id>/pdf")
def download_pdf_report(history_id):
    analysis = get_history_by_id(history_id)
    if not analysis:
        abort(404)

    pdf_buffer = generate_pdf_report(analysis)
    clean_name = os.path.splitext(analysis["filename"])[0]
    out_filename = f"BriefIQ_Report_{clean_name}.pdf"

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=out_filename,
        mimetype="application/pdf"
    )


@app.route("/download-report/<int:history_id>/txt")
def download_txt_report(history_id):
    analysis = get_history_by_id(history_id)
    if not analysis:
        abort(404)

    lines = [
        "=" * 70,
        "BRIEFIQ - AI SUMMARY & REPORT GENERATOR",
        f"Document: {analysis['filename']}",
        f"Date: {analysis.get('created_at')}",
        f"Analysis Type: {analysis.get('analysis_type', '').title()}",
        "=" * 70,
        "",
        "EXECUTIVE SUMMARY:",
        analysis.get("summary_content", "No summary content available."),
        "",
    ]

    if analysis.get("kpis"):
        lines.append("METRICS & KPIS:")
        for k, v in analysis["kpis"].items():
            lines.append(f" - {k.replace('_', ' ').title()}: {v}")
        lines.append("")

    if analysis.get("individual_summaries"):
        lines.append("INDIVIDUAL RECORDS / ADVISORY:")
        for s in analysis["individual_summaries"]:
            lines.append(f" - {s.get('name')}: Score {s.get('score')} | Status: {s.get('performance')}")
            lines.append(f"   Advisory: {s.get('report')}")
        lines.append("")

    from io import BytesIO
    content = "\n".join(lines).encode("utf-8")
    buf = BytesIO(content)
    clean_name = os.path.splitext(analysis["filename"])[0]

    return send_file(
        buf,
        as_attachment=True,
        download_name=f"BriefIQ_Summary_{clean_name}.txt",
        mimetype="text/plain"
    )


@app.route("/delete-history/<int:history_id>", methods=["POST"])
def delete_history(history_id):
    user_id = session.get("user_id")
    delete_history_item(history_id, user_id=user_id)
    flash("Analysis record removed from your history.", "info")
    return redirect(url_for("profile"))


# ==========================================================
# CHAT WITH DOCUMENT
# ==========================================================

@app.route("/chat/<int:history_id>", methods=["POST"])
def chat(history_id):
    """AJAX endpoint: answer a user question about a document's summary."""
    from flask import jsonify
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"answer": "Please type a question.", "confidence": "low"})

    analysis = get_history_by_id(history_id)
    if not analysis:
        return jsonify({"answer": "Document not found.", "confidence": "low"})

    summary = analysis.get("summary_content") or ""

    # Build extra context from individual summaries (for dataset reports)
    extra_context = ""
    if analysis.get("individual_summaries"):
        parts = []
        for s in analysis["individual_summaries"]:
            parts.append(
                f"{s.get('name','')}: score {s.get('score','')}, "
                f"performance {s.get('performance','')}, {s.get('report','')}"
            )
        extra_context = " ".join(parts)

    result = answer_question(question, summary, context=extra_context)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)