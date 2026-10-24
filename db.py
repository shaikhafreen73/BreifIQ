import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "briefiq.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Document analysis history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_kb REAL DEFAULT 0,
            analysis_type TEXT NOT NULL,
            summary_title TEXT,
            summary_content TEXT,
            kpis_json TEXT,
            chart_data_json TEXT,
            table_data_json TEXT,
            individual_summaries_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def create_user(username, email, password, full_name, role="Student"):
    conn = get_db()
    cursor = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, (username.strip(), email.strip().lower(), pw_hash, full_name.strip(), role))
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            return {"success": False, "error": "Username already taken. Please choose another."}
        elif "email" in err_msg:
            return {"success": False, "error": "Email already registered. Please login instead."}
        return {"success": False, "error": "Registration failed. User already exists."}
    finally:
        conn.close()


def authenticate_user(username_or_email, password):
    conn = get_db()
    cursor = conn.cursor()
    identifier = username_or_email.strip().lower()
    cursor.execute("""
        SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?
    """, (identifier, identifier))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_profile(user_id, full_name, role):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET full_name = ?, role = ? WHERE id = ?
    """, (full_name.strip(), role, user_id))
    conn.commit()
    conn.close()


def save_analysis(user_id, filename, file_type, file_size_kb, analysis_type,
                  summary_title, summary_content, kpis=None, chart_data=None,
                  table_data=None, individual_summaries=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (
            user_id, filename, file_type, file_size_kb, analysis_type,
            summary_title, summary_content, kpis_json, chart_data_json,
            table_data_json, individual_summaries_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        filename,
        file_type,
        file_size_kb,
        analysis_type,
        summary_title,
        summary_content,
        json.dumps(kpis) if kpis else None,
        json.dumps(chart_data) if chart_data else None,
        json.dumps(table_data) if table_data else None,
        json.dumps(individual_summaries) if individual_summaries else None
    ))
    conn.commit()
    history_id = cursor.lastrowid
    conn.close()
    return history_id


def get_history_by_id(history_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE id = ?", (history_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("kpis_json"):
        d["kpis"] = json.loads(d["kpis_json"])
    if d.get("chart_data_json"):
        d["chart_data"] = json.loads(d["chart_data_json"])
    if d.get("table_data_json"):
        d["table_data"] = json.loads(d["table_data_json"])
    if d.get("individual_summaries_json"):
        d["individual_summaries"] = json.loads(d["individual_summaries_json"])
    return d


def get_user_history(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT id, filename, file_type, file_size_kb, analysis_type,
                   summary_title, created_at
            FROM history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT id, filename, file_type, file_size_kb, analysis_type,
                   summary_title, created_at
            FROM history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    filter_clause = "WHERE user_id = ?" if user_id else ""
    params = (user_id,) if user_id else ()

    cursor.execute(f"SELECT COUNT(*) FROM history {filter_clause}", params)
    total_docs = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM history {filter_clause} {'AND' if user_id else 'WHERE'} analysis_type = 'summary'", params)
    total_summaries = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM history {filter_clause} {'AND' if user_id else 'WHERE'} analysis_type = 'dataset'", params)
    total_reports = cursor.fetchone()[0]

    conn.close()
    return {
        "total_documents": total_docs,
        "total_summaries": total_summaries,
        "total_reports": total_reports,
        "time_saved_hours": round(total_docs * 0.45, 1)
    }


def delete_history_item(history_id, user_id=None):
    conn = get_db()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM history WHERE id = ? AND user_id = ?", (history_id, user_id))
    else:
        cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()
