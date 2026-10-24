import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_pdf_report(analysis_data):
    """
    Builds a professional branded PDF report in memory using ReportLab.
    Returns BytesIO buffer.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    brand_title_style = ParagraphStyle(
        'BrandTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e1b4b')
    )

    brand_subtitle_style = ParagraphStyle(
        'BrandSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6366f1')
    )

    heading1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    summary_box_style = ParagraphStyle(
        'SummaryBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#1e293b')
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=15,
        spaceBefore=4
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )

    meta_val = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Header / Branding
    story.append(Paragraph("BriefIQ", brand_title_style))
    story.append(Paragraph("AI SUMMARY & REPORT GENERATOR • DEEP LEARNING INTELLIGENCE", brand_subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceBefore=2, spaceAfter=14))

    # Document Meta Table
    filename = analysis_data.get("filename", "Uploaded_Document")
    analysis_type = analysis_data.get("analysis_type", "summary").title()
    created_at = analysis_data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    meta_table_data = [
        [Paragraph("Document Name:", meta_label), Paragraph(filename, meta_val),
         Paragraph("Analysis Date:", meta_label), Paragraph(str(created_at), meta_val)],
        [Paragraph("Analysis Engine:", meta_label), Paragraph("Google T5 Deep Learning Transformer", meta_val),
         Paragraph("Report Type:", meta_label), Paragraph(f"{analysis_type} Report", meta_val)]
    ]

    meta_table = Table(meta_table_data, colWidths=[110, 160, 100, 160])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Executive AI Summary Section
    story.append(Paragraph("Executive Summary & Core Insights", heading1_style))
    
    summary_text = analysis_data.get("summary_content") or analysis_data.get("ai_summary") or "No summary content available."
    summary_p = Paragraph(summary_text, summary_box_style)
    
    summary_table = Table([[summary_p]], colWidths=[530])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#86efac')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Takeaways or KPIs
    kpis = analysis_data.get("kpis") or {}
    if kpis:
        story.append(Paragraph("Key Performance Indicators (KPIs)", heading1_style))
        kpi_cells = []
        for k, v in list(kpis.items())[:6]:
            label = k.replace("_", " ").title()
            kpi_cells.append(Paragraph(f"<b>{label}:</b> {v}", body_style))

        # Arrange in rows of 2
        kpi_grid = []
        for i in range(0, len(kpi_cells), 2):
            row = kpi_cells[i:i+2]
            if len(row) == 1:
                row.append(Paragraph("", body_style))
            kpi_grid.append(row)

        if kpi_grid:
            kpi_table = Table(kpi_grid, colWidths=[265, 265])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 14))

    # Individual summaries / Student performance report if present
    ind_summaries = analysis_data.get("individual_summaries") or []
    if ind_summaries:
        story.append(Paragraph("Detailed Segment & Performance Records", heading1_style))
        records_data = [
            [Paragraph("<b>Entity / Student</b>", meta_label),
             Paragraph("<b>Score / Value</b>", meta_label),
             Paragraph("<b>Status</b>", meta_label),
             Paragraph("<b>Advisory Assessment</b>", meta_label)]
        ]

        for s in ind_summaries[:15]:
            records_data.append([
                Paragraph(str(s.get("name", "N/A")), body_style),
                Paragraph(str(s.get("score", "N/A")), body_style),
                Paragraph(str(s.get("performance", "N/A")), body_style),
                Paragraph(str(s.get("report", "N/A")), body_style)
            ])

        records_table = Table(records_data, colWidths=[120, 80, 90, 240])
        records_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(records_table)
        story.append(Spacer(1, 14))

    # Footer note
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=5, spaceAfter=8))
    footer_text = "Generated automatically by BriefIQ Deep Learning Platform • Confidential & Protected"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer
