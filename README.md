# 🧠 BriefIQ — AI Document Summarization & Dataset Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![Hugging Face](https://img.shields.io/badge/Transformers-T5--small-yellow.svg)](https://huggingface.co/google-t5/t5-small)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**BriefIQ** is an AI-powered document summarization and exploratory data analysis (EDA) web application built as a **Capstone Project**. It leverages Deep Learning (**Google T5-small transformer**) to distill lengthy documents and automatically analyzes structured datasets into actionable KPIs, interactive charts, and downloadable reports.

---

## ✨ Key Features

- **🤖 Deep Learning Document Summarization**:
  - Utilizes Google's **T5-small** sequence-to-sequence transformer model.
  - Automatically handles chunking and multi-pass synthesis for large documents.
  - Extracts key takeaways and computes reading-time metrics (words reduced, reading time saved).
  - Multi-tier summary modes: *Concise*, *Executive*, and *Detailed*.

- **📊 Automated Dataset Analytics**:
  - Auto-detects academic datasets (grades, attendance, performance tiers) with personalized student advisories.
  - Computes statistical summaries (mean, min, max, top categories) for general business datasets.
  - Generates interactive **Chart.js** visualizations (doughnut, pie, and bar charts).

- **💬 Offline Document Chat Engine**:
  - Built-in extractive Q&A engine using TF-IDF sentence ranking.
  - Ask questions directly about your uploaded documents completely offline.

- **📑 Branded PDF & TXT Report Generation**:
  - Generates professional, publication-ready PDF reports on-the-fly using **ReportLab** (in-memory, zero disk clutter).
  - Export plain text summary breakdowns.

- **🔐 User Profiles & History Management**:
  - Session-based authentication with PBKDF2 password hashing.
  - Full history log tracking past analyses, metrics, and time saved.
  - 1-click **Demo Login** for quick testing.

---

## 🛠️ Supported File Formats

| Category | Formats | Engine / Library |
|---|---|---|
| **Documents** | `.pdf` | PyMuPDF (`fitz`) |
| | `.docx` | `python-docx` |
| | `.txt`, `.md`, `.log`, `.rtf` | Native Python IO (multi-encoding) |
| **Datasets** | `.csv`, `.tsv` | `pandas` |
| | `.xlsx`, `.xls` | `pandas` + `openpyxl` |
| | `.json` | `json` + `pandas` |

---

## 📁 Project Architecture

```
Capstone-Project/
├── app.py                  # Main Flask application and routing
├── db.py                   # SQLite database operations & user authentication
├── summarizer.py           # Deep Learning summarization pipeline (Google T5-small)
├── data_analyzer.py        # Automated EDA & dataset metrics computation
├── document_processor.py   # Multi-format document parser
├── excel_reader.py         # Tabular data ingestion (CSV / Excel / TSV)
├── pdf_reader.py           # PyMuPDF text & metadata extraction
├── report_generator.py     # In-memory branded PDF report builder (ReportLab)
├── chat_engine.py          # TF-IDF extractive document Q&A engine
├── create_samples.py       # Demo test data generator
├── test_app.py             # Integration & unit test suite
├── requirements.txt        # Project dependencies
├── Templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout & navbar
│   ├── index.html          # Upload dashboard & sample cards
│   ├── login.html          # Authentication & demo login
│   ├── register.html       # User registration
│   ├── profile.html        # User history & profile settings
│   ├── result.html         # Analysis results & Chart.js dashboards
│   └── about.html          # Project information & architecture
├── Static/
│   ├── css/style.css       # Custom modern responsive stylesheet
│   └── js/main.js          # Chart.js rendering & drag-and-drop UI
├── samples/                # Pre-packaged demo files
└── Uploads/                # Temporary user upload directory
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/shaikhafreen73/Capstone-Project.git
cd Capstone-Project
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🔑 Demo Access
You can log in instantly using the demo credentials:
- **Username**: `demo_user`
- **Password**: `demo123`
- Or simply click the **"Demo Login"** button on the login screen.

---

## 🧪 Running Tests

To verify that the application and all dependencies are working properly:
```bash
python test_app.py
```

---

## 📜 Tech Stack

- **Backend**: Python 3.10+, Flask 3.0+
- **Deep Learning / NLP**: Hugging Face `transformers`, PyTorch, Google T5-small, SentencePiece
- **Data Analytics**: Pandas, NumPy
- **Document Processing**: PyMuPDF, python-docx, openpyxl
- **Reporting**: ReportLab
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism design), JavaScript, Chart.js
- **Database**: SQLite3
