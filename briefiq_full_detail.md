# 🧠 BriefIQ — Full Application Breakdown

> **BriefIQ** is an AI-powered document summarization and dataset analysis web app built as a **Capstone Project**. It uses Deep Learning (Google T5-small transformer) to summarize documents and performs automated exploratory data analysis on spreadsheets and CSVs.

---

## 📁 Project Structure

```
BreifIQ/
├── app.py                  ← Main Flask app (routes, request handling)
├── db.py                   ← SQLite database layer
├── summarizer.py           ← T5-small NLP summarization engine
├── data_analyzer.py        ← Pandas/NumPy dataset analytics engine
├── document_processor.py   ← File parsing (PDF, DOCX, TXT, etc.)
├── excel_reader.py         ← CSV/XLSX/TSV reader
├── pdf_reader.py           ← PyMuPDF-based PDF text extractor
├── report_generator.py     ← ReportLab branded PDF report builder
├── create_samples.py       ← Script to generate demo sample files
├── test_app.py             ← App unit/integration tests
├── briefiq.db              ← SQLite database file
├── requirements.txt        ← Python dependencies
├── Templates/              ← HTML Jinja2 templates (Frontend)
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── result.html
│   └── about.html
├── Static/
│   ├── css/style.css       ← Main stylesheet (~50KB, full custom CSS)
│   └── js/main.js          ← Frontend JavaScript (~10KB)
├── Uploads/                ← Temporary uploaded files
├── Reports/                ← Generated reports (if saved to disk)
└── samples/                ← Pre-built demo files
```

---

## 🖥️ FRONTEND

### Templates (Jinja2 HTML)

| File | Purpose |
|---|---|
| `base.html` | Master layout — navbar, flash messages, footer, font imports |
| `index.html` | Home page — upload form, recent history, stats dashboard |
| `login.html` | Login form with demo login button |
| `register.html` | Registration form (name, username, email, role, password) |
| `profile.html` | User profile page — history table, stats, edit profile |
| `result.html` | Analysis result page — summary, KPIs, charts, table data |
| `about.html` | About page — project info, tech stack |

### Styling (`Static/css/style.css` — ~50KB)
- **100% Vanilla CSS** — no Tailwind, no Bootstrap
- Dark/gradient themed design
- Custom cards, badges, progress bars
- Responsive layout
- Glassmorphism effects on cards
- Animated transitions and hover effects

### JavaScript (`Static/js/main.js` — ~10KB)
- **Chart.js** integration — renders doughnut, pie, and bar charts dynamically from JSON data
- File upload drag-and-drop UI
- Flash message auto-dismiss
- Form validation on the client side
- Dynamic UI interactions (tab switching, loading states)

---

## ⚙️ BACKEND

### Framework
- **Python Flask** (`flask>=3.0.0`) running on port **5000**
- Server-side rendering using **Jinja2** templates
- Session-based authentication (Flask `session`)
- Werkzeug for password hashing and file security

### Routes in `app.py`

| Method | Route | Description |
|---|---|---|
| GET/POST | `/login` | Login form + authentication |
| POST | `/demo-login` | One-click demo login as "Alex Morgan" |
| GET/POST | `/register` | User registration |
| GET | `/logout` | Clears session, redirects to login |
| GET | `/` | Home page with recent history & stats |
| GET | `/about` | About page |
| GET/POST | `/profile` | User profile + edit full name/role |
| POST | `/upload` | File upload & analysis trigger |
| GET/POST | `/sample/<type>` | Load pre-built demo files (pdf/csv/excel/docx) |
| GET | `/result/<id>` | View a specific analysis result |
| GET | `/result` | Redirect to most recent result |
| GET | `/download-report/<id>/pdf` | Download PDF report |
| GET | `/download-report/<id>/txt` | Download plain text report |
| POST | `/delete-history/<id>` | Delete a history record |

---

## 🗄️ DATABASE (`db.py`)

- **SQLite** — single file `briefiq.db`, zero external DB server needed
- Uses Python's built-in `sqlite3` module
- `werkzeug.security` for password hashing (PBKDF2)

### Tables

#### `users`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `username` | TEXT UNIQUE | Login username |
| `email` | TEXT UNIQUE | Email address |
| `password_hash` | TEXT | Bcrypt/PBKDF2 hashed password |
| `full_name` | TEXT | Display name |
| `role` | TEXT | Student / Researcher / etc. |
| `created_at` | TIMESTAMP | Registration timestamp |

#### `history`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | INTEGER FK | Links to users table |
| `filename` | TEXT | Original uploaded filename |
| `file_type` | TEXT | PDF, DOCX, CSV, XLSX, etc. |
| `file_size_kb` | REAL | File size in KB |
| `analysis_type` | TEXT | `"summary"` or `"dataset"` |
| `summary_title` | TEXT | Auto-generated report title |
| `summary_content` | TEXT | Full AI-generated summary text |
| `kpis_json` | TEXT | JSON blob of KPI metrics |
| `chart_data_json` | TEXT | JSON blob for chart rendering |
| `table_data_json` | TEXT | JSON blob of tabular rows |
| `individual_summaries_json` | TEXT | JSON blob of per-record reports |
| `created_at` | TIMESTAMP | Analysis timestamp |

### DB Functions
- `init_db()` — Creates tables + inserts default demo user
- `create_user()` — Registers new user with hashed password
- `authenticate_user()` — Validates login (username OR email)
- `get_user_by_id()` — Fetch user by session ID
- `update_user_profile()` — Edit full_name & role
- `save_analysis()` — Persist an analysis result to history
- `get_history_by_id()` — Fetch one result with JSON parsing
- `get_user_history()` — List user's past analyses
- `get_user_stats()` — Count docs/summaries/reports + time saved
- `delete_history_item()` — Remove a record from history

---

## 🤖 AI / DEEP LEARNING (`summarizer.py`)

### Model: **Google T5-small** (Text-to-Text Transfer Transformer)
- Loaded lazily on first use (not at startup) to keep boot fast
- Uses **Hugging Face `transformers`** `pipeline("text2text-generation")`
- `sentencepiece` used for tokenization

### Pipeline
1. **Clean text** — strip whitespace/artifacts
2. **Chunk splitting** — split into ~220-word chunks at sentence boundaries to fit T5's token window
3. **Chunk-by-chunk inference** — each chunk passed as `"summarize: <text>"`
4. **Synthesis pass** — if multiple chunks, run another T5 pass to merge them
5. **Fallback** — if T5 fails/unavailable, uses an **extractive summarizer** (word-frequency TF-IDF-style scoring)

### Summary Modes
| Mode | Max Tokens | Min Tokens |
|---|---|---|
| `concise` | 90 | 25 |
| `detailed` | 220 | 60 |
| `executive` | 180 | 50 |

### Output of `analyze_document_text()`
```python
{
  "summary": "...",           # T5 generated text
  "takeaways": [...],         # 4 key bullet sentences
  "metrics": {
    "original_word_count": N,
    "summary_word_count": N,
    "reduction_percentage": N,
    "original_reading_time_mins": N,
    "summary_reading_time_mins": N,
    "time_saved_mins": N,
    "model_used": "Google T5-small ..."
  }
}
```

---

## 📊 DATA ANALYTICS (`data_analyzer.py`)

### Supports Two Dataset Types

#### 1. Academic / Student Datasets
Auto-detects columns like `attendance`, `overall score`, `performance`, `student name`.

**Outputs:**
- Average attendance %
- Average score %
- Performance distribution (Excellent / Very Good / Good / Average / Needs Improvement)
- Per-student personalized advisory report (with attendance-based warnings)
- Chart 1: **Doughnut chart** — performance tier distribution
- Chart 2: **Bar chart** — top 10 students by score

#### 2. General Business / Analytical Datasets
For any other CSV/Excel file.

**Outputs:**
- Primary numeric metric stats (mean, min, max)
- Top categorical value frequency
- Chart 1: **Pie chart** — category distribution
- Chart 2: **Bar chart** — top 10 rows comparison
- Sample record summaries (first 15 rows)

---

## 📄 FILE PROCESSING

### `document_processor.py`
| Extension | Library Used |
|---|---|
| `.pdf` | PyMuPDF (`fitz` / `pymupdf`) via `pdf_reader.py` |
| `.docx` | `python-docx` |
| `.txt`, `.md`, `.log`, `.html`, `.py`, etc. | Native Python `open()` with multi-encoding fallback |

### `excel_reader.py`
| Extension | Library |
|---|---|
| `.csv` | `pandas.read_csv()` with multi-encoding fallback |
| `.tsv` | `pandas.read_csv(sep='\t')` |
| `.xlsx` / `.xls` | `pandas.read_excel()` via `openpyxl` |
| `.json` | `json.load()` → `pd.DataFrame()` |

---

## 📑 PDF REPORT GENERATOR (`report_generator.py`)

Uses **ReportLab** to generate professional branded PDFs **in-memory** (no disk write):

- **BriefIQ** branded header with purple accent line
- Document metadata table (filename, date, engine, type)
- **Executive Summary** box (green background)
- **KPI grid** (2-column layout)
- **Individual Records Table** (student or row-level data, up to 15 rows)
- Footer: "Generated automatically by BriefIQ Deep Learning Platform"

---

## 🔐 AUTHENTICATION SYSTEM

- **Session-based** — Flask `session` stores `user_id`, `username`, `full_name`, `role`
- Passwords hashed with `werkzeug.security.generate_password_hash` (PBKDF2-SHA256)
- Login accepts **username OR email**
- **Demo login** — one-click login as `demo_user` / `demo123` (pre-seeded in DB)
- Protected routes redirect to `/login` if not authenticated
- `inject_user()` context processor makes `current_user` available in all templates

---

## 📦 DEPENDENCIES (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| `flask` | ≥3.0.0 | Web framework |
| `transformers` | ≥4.40.0 | Hugging Face T5 model |
| `torch` | ≥2.0.0 | PyTorch backend for T5 |
| `sentencepiece` | ≥0.2.0 | T5 tokenizer |
| `pymupdf` | ≥1.24.0 | PDF text extraction |
| `pandas` | ≥2.2.0 | Data analysis |
| `openpyxl` | ≥3.1.0 | Excel file support |
| `python-docx` | ≥1.1.0 | DOCX file parsing |
| `reportlab` | ≥4.0.0 | PDF report generation |

---

## 🔄 Full Request Flow (Document Upload)

```
User uploads file → POST /upload
  ↓
is_tabular_file()?
  ├── YES (CSV/XLSX) → excel_reader.read_file() → pandas DataFrame
  │     └── data_analyzer.analyze_dataset() → KPIs + charts + per-row summaries
  └── NO (PDF/DOCX/TXT) → document_processor.process_document() → raw text
        └── summarizer.analyze_document_text() → T5 summary + takeaways + metrics
              ↓
          db.save_analysis() → writes to SQLite history table
              ↓
          redirect to /result/<history_id>
              ↓
          result.html renders charts (Chart.js) + summary + KPI cards + table
```

---

## 📋 Sample Files (Demo Mode)

| Sample | Type | Description |
|---|---|---|
| `sample_ai_research.pdf` | Document | AI research paper demo |
| `sample_student_grades.csv` | Dataset | Student grades with attendance |
| `sample_sales_analytics.xlsx` | Dataset | Business sales data |
| `sample_executive_brief.docx` | Document | Corporate executive brief |

Generated by `create_samples.py` on first use if not present.

---

## 🌐 Pages Summary

| Page | URL | Access |
|---|---|---|
| Home / Upload | `/` | Public |
| Login | `/login` | Public |
| Register | `/register` | Public |
| Profile & History | `/profile` | 🔒 Login Required |
| Result View | `/result/<id>` | Public |
| About | `/about` | Public |
| Download PDF | `/download-report/<id>/pdf` | Public |
| Download TXT | `/download-report/<id>/txt` | Public |
