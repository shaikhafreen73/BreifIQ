import pandas as pd
import numpy as np


def analyze_dataset(df):
    """
    Performs comprehensive automated exploratory data analysis and AI report generation
    for both academic (student) and general datasets.
    """
    total_records = len(df)
    columns = df.columns.tolist()
    missing_count = int(df.isnull().sum().sum())

    # Replace NaN for clean JSON / table serialization
    clean_df = df.fillna("N/A")
    rows = clean_df.astype(str).values.tolist()

    # Column classification
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string', str]).columns.tolist()

    # Detect Academic / Student Dataset Columns
    attendance_col = None
    overall_col = None
    performance_col = None
    name_col = None

    for col in columns:
        col_lower = str(col).lower().strip()
        if "attendance" in col_lower:
            attendance_col = col
        if ("overall" in col_lower and "score" in col_lower) or col_lower in ["score", "grade", "marks", "total", "percentage"]:
            overall_col = col
        if "performance" in col_lower or col_lower in ["result", "status"]:
            performance_col = col
        if ("student" in col_lower and "name" in col_lower) or col_lower in ["name", "student", "full name", "candidate"]:
            name_col = col

    is_student_data = (overall_col is not None or attendance_col is not None or (name_col is not None and performance_col is not None))

    kpis = {
        "total_records": total_records,
        "total_columns": len(columns),
        "missing_values": missing_count,
        "dataset_type": "Academic & Performance" if is_student_data else "General Business / Analytical"
    }

    individual_summaries = []
    chart_data = {}
    summary_parts = []

    # ==========================================================
    # ACADEMIC / STUDENT DATASET ANALYSIS
    # ==========================================================
    if is_student_data:
        summary_parts.append(f"The dataset contains {total_records} student records across {len(columns)} tracked attributes.")

        avg_attendance = None
        if attendance_col and pd.to_numeric(df[attendance_col], errors='coerce').notnull().any():
            avg_attendance = pd.to_numeric(df[attendance_col], errors='coerce').mean()
            kpis["avg_attendance"] = f"{avg_attendance:.1f}%"
            summary_parts.append(f"The cohort average attendance rate stands at {avg_attendance:.2f}%.")

        avg_score = None
        if overall_col and pd.to_numeric(df[overall_col], errors='coerce').notnull().any():
            numeric_scores = pd.to_numeric(df[overall_col], errors='coerce')
            avg_score = numeric_scores.mean()
            kpis["avg_score"] = f"{avg_score:.1f}%"
            summary_parts.append(f"The class average overall score is {avg_score:.2f}%.")

        # Performance distribution
        perf_distribution = {}
        if performance_col:
            perf_counts = df[performance_col].value_counts().to_dict()
            perf_distribution = {str(k): int(v) for k, v in perf_counts.items()}
            dist_str = ", ".join(f"{k}: {v}" for k, v in perf_distribution.items())
            summary_parts.append(f"Cohort Performance distribution: {dist_str}.")

        # Generate per-student personalized advisory summaries
        for idx, row in df.iterrows():
            student_name = str(row[name_col]) if name_col else f"Student {idx + 1}"

            # Score
            score_val = None
            if overall_col:
                try:
                    score_val = float(row[overall_col])
                except (ValueError, TypeError):
                    score_val = None

            # Attendance
            att_val = None
            if attendance_col:
                try:
                    att_val = float(row[attendance_col])
                except (ValueError, TypeError):
                    att_val = None

            # Determine performance classification
            if score_val is not None:
                if score_val >= 90:
                    perf = "Excellent"
                elif score_val >= 80:
                    perf = "Very Good"
                elif score_val >= 70:
                    perf = "Good"
                elif score_val >= 60:
                    perf = "Average"
                else:
                    perf = "Needs Improvement"
            elif performance_col and str(row[performance_col]) != "nan":
                perf = str(row[performance_col])
            else:
                perf = "Recorded"

            # Advisory Narrative
            if score_val is not None and score_val >= 90:
                report = "Outstanding academic performance."
                if att_val is not None and att_val < 75:
                    report += f" Note: Attendance ({att_val}%) is below recommended 75% threshold."
                else:
                    report += " Consistently demonstrates mastery across core coursework."
            elif score_val is not None and score_val >= 80:
                report = "Strong academic consistency and high conceptual understanding."
                if att_val is not None and att_val < 75:
                    report += f" Recommended action: prioritize lecture attendance ({att_val}%)."
            elif score_val is not None and score_val >= 70:
                report = "Competent understanding; encourage targeted practice on challenging topics."
                if att_val is not None and att_val < 75:
                    report += " Improving attendance will directly boost grades."
            elif score_val is not None and score_val >= 60:
                report = "Satisfactory progress, but additional revision and mentoring suggested."
            elif score_val is not None:
                report = "Immediate academic intervention and study group support recommended."
            else:
                report = "Record verified. Evaluation metrics logged."

            individual_summaries.append({
                "name": student_name,
                "score": f"{score_val:.1f}%" if score_val is not None else "N/A",
                "attendance": f"{att_val:.1f}%" if att_val is not None else "N/A",
                "performance": perf,
                "report": report
            })

        # Chart Data
        # Chart 1: Performance Distribution Doughnut
        if perf_distribution:
            chart_data["distribution"] = {
                "type": "doughnut",
                "title": "Performance Tier Distribution",
                "labels": list(perf_distribution.keys()),
                "data": list(perf_distribution.values())
            }
        elif overall_col and numeric_cols:
            # Bucket scores into tiers
            scores = pd.to_numeric(df[overall_col], errors='coerce').dropna()
            tiers = {
                "Excellent (>=90)": int((scores >= 90).sum()),
                "Very Good (80-89)": int(((scores >= 80) & (scores < 90)).sum()),
                "Good (70-79)": int(((scores >= 70) & (scores < 80)).sum()),
                "Average (60-69)": int(((scores >= 60) & (scores < 70)).sum()),
                "Needs Help (<60)": int((scores < 60).sum())
            }
            tiers = {k: v for k, v in tiers.items() if v > 0}
            chart_data["distribution"] = {
                "type": "doughnut",
                "title": "Grade Distribution Tiers",
                "labels": list(tiers.keys()),
                "data": list(tiers.values())
            }

        # Chart 2: Top Students / Scores Bar Chart
        if overall_col and name_col:
            top_df = df.dropna(subset=[overall_col]).sort_values(by=overall_col, ascending=False).head(10)
            chart_data["comparison"] = {
                "type": "bar",
                "title": "Top Students by Overall Score",
                "labels": [str(x) for x in top_df[name_col].tolist()],
                "data": [float(x) for x in pd.to_numeric(top_df[overall_col], errors='coerce').tolist()]
            }

    # ==========================================================
    # GENERAL TABULAR DATASET ANALYSIS
    # ==========================================================
    else:
        summary_parts.append(
            f"The uploaded dataset contains {total_records} rows and {len(columns)} attributes."
        )

        # Numerical statistics
        if numeric_cols:
            primary_num = numeric_cols[0]
            col_mean = df[primary_num].mean()
            col_min = df[primary_num].min()
            col_max = df[primary_num].max()
            kpis["primary_metric"] = f"{primary_num}: {col_mean:.2f}"
            summary_parts.append(
                f"The key numerical metric '{primary_num}' shows an average of {col_mean:.2f} (ranging from {col_min:.2f} to {col_max:.2f})."
            )

        # Categorical statistics
        if categorical_cols:
            primary_cat = categorical_cols[0]
            top_val = df[primary_cat].mode()[0] if not df[primary_cat].empty else "None"
            counts = df[primary_cat].value_counts().head(6).to_dict()
            summary_parts.append(
                f"For category '{primary_cat}', '{top_val}' is the most frequent value."
            )
            chart_data["distribution"] = {
                "type": "pie",
                "title": f"Distribution by {primary_cat}",
                "labels": [str(k) for k in counts.keys()],
                "data": [int(v) for v in counts.values()]
            }

        # Secondary chart
        if len(numeric_cols) > 0 and len(columns) > 1:
            label_col = categorical_cols[0] if categorical_cols else columns[0]
            val_col = numeric_cols[0]
            sub_df = df.head(10)
            chart_data["comparison"] = {
                "type": "bar",
                "title": f"Sample Comparison: {val_col} across {label_col}",
                "labels": [str(x)[:15] for x in sub_df[label_col].tolist()],
                "data": [float(x) if pd.notnull(x) else 0 for x in pd.to_numeric(sub_df[val_col], errors='coerce').tolist()]
            }

        # Generate sample record summaries
        for idx, row in df.head(15).iterrows():
            col1 = columns[0]
            col2 = columns[1] if len(columns) > 1 else col1
            individual_summaries.append({
                "name": f"Record #{idx + 1} ({row[col1]})",
                "score": f"{row[col2]}",
                "performance": "Analyzed",
                "report": f"Attribute '{col1}': {row[col1]} | '{col2}': {row[col2]}."
            })

    ai_summary = " ".join(summary_parts)

    return {
        "is_student_data": is_student_data,
        "kpis": kpis,
        "ai_summary": ai_summary,
        "columns": columns,
        "rows": rows,
        "chart_data": chart_data,
        "individual_summaries": individual_summaries
    }
