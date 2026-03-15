"""
Report Generator — Creates a downloadable PDF health summary using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime


class ReportGenerator:
    """
    Generates a professional PDF health summary report for a scan session.
    """

    RISK_COLORS = {
        'GREEN': colors.HexColor('#22c55e'),
        'YELLOW': colors.HexColor('#f59e0b'),
        'RED': colors.HexColor('#ef4444'),
    }

    # ✅ Removed anemia & dehydration
    CONDITION_LABELS = {
        'jaundice': '🟡 Jaundice',
        'anemia': '🩸 Anemia',
    }

    def generate_pdf(self, session_data, risk_data, recommendations):

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        story = []

        # ── Styles ───────────────────────────────
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=2,
            alignment=TA_CENTER,
        )
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155'),
            leading=16,
        )
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#334155'),
            leftIndent=16,
            leading=16,
            spaceAfter=3,
        )

        # ── Header ───────────────────────────────
        story.append(Paragraph('🩺 NUTRI-SCAN', title_style))
        story.append(Paragraph('AI-Powered Nutritional Health Screening Report', subtitle_style))
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 6 * mm))

        # ── Session Info ─────────────────────────
        scan_date = session_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
        if hasattr(scan_date, 'strftime'):
            scan_date = scan_date.strftime('%d %B %Y, %H:%M')

        session_id = str(session_data.get('session_id', 'N/A'))[:8].upper()

        info_data = [
            ['Report Date:', datetime.now().strftime('%d %B %Y')],
            ['Scan Date:', scan_date],
            ['Session ID:', session_id],
            ['Scan Type:', 'Facial Visual Analysis + Symptom Assessment'],
        ]

        info_table = Table(info_data, colWidths=[55 * mm, 110 * mm])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#475569')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8 * mm))

        # ── Risk Level ───────────────────────────
        story.append(Paragraph('OVERALL RISK ASSESSMENT', section_header_style))

        risk_level = risk_data.get('risk_level', 'GREEN')
        risk_color = self.RISK_COLORS.get(risk_level, colors.green)
        risk_label = risk_data.get('risk_label', 'Low Risk')
        risk_desc = risk_data.get('risk_description', '')
        overall_score = risk_data.get('overall_score', 0)

        risk_data_table = [
            [f'Risk Level: {risk_label}', f'Score: {overall_score}/10'],
        ]
        risk_table = Table(risk_data_table, colWidths=[120 * mm, 45 * mm])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), risk_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(risk_desc, body_style))
        story.append(Spacer(1, 6 * mm))

        # ── Condition Scores ─────────────────────
        story.append(Paragraph('VISUAL ANALYSIS SCORES', section_header_style))

        visual = session_data.get('visual_analysis', {})
        combined = session_data.get('combined_scores', visual)

        score_rows = [['Condition', 'Visual Score', 'Combined Score', 'Risk']]

        for condition, label in self.CONDITION_LABELS.items():
            vis_score = visual.get(f'{condition}_score', visual.get(condition, 0))
            comb_score = combined.get(condition, vis_score)

            if comb_score >= 5:
                risk_ind = '🔴 High'
            elif comb_score >= 3:
                risk_ind = '🟡 Moderate'
            else:
                risk_ind = '🟢 Low'

            score_rows.append([
                label.replace('🟡 ', '').replace('🍊 ', ''),
                f'{vis_score}/10',
                f'{comb_score}/10',
                risk_ind
            ])

        score_table = Table(score_rows, colWidths=[70 * mm, 35 * mm, 40 * mm, 25 * mm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 6 * mm))

        # ── Detected Conditions ──────────────────
        detected = risk_data.get('detected_conditions', [])
        if detected:
            story.append(Paragraph('DETECTED INDICATORS', section_header_style))
            for cond in detected:
                story.append(Paragraph(f'• {cond}', bullet_style))
            story.append(Spacer(1, 4 * mm))

        # ── Recommendations ──────────────────────
        story.append(Paragraph('PERSONALIZED RECOMMENDATIONS', section_header_style))

        # ✅ Removed hydration section
        rec_sections = [
            ('🥗 Dietary Recommendations', recommendations.get('dietary', [])),
            ('🏃 Lifestyle Recommendations', recommendations.get('lifestyle', [])),
            ('🏥 Medical Advisory', recommendations.get('medical', [])),
        ]

        for section_title, items in rec_sections:
            if items:
                story.append(Paragraph(section_title, ParagraphStyle(
                    'SubSection',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#0f172a'),
                    fontName='Helvetica-Bold',
                    spaceBefore=8,
                    spaceAfter=4,
                )))
                for item in items:
                    story.append(Paragraph(f'• {item}', bullet_style))

        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 4 * mm))

        # ── Disclaimer ───────────────────────────
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            leading=12,
        )

        story.append(Paragraph(
            '⚠️ DISCLAIMER: This report is generated by an AI screening tool for preliminary assessment purposes only. '
            'It is NOT a medical diagnosis. Always consult a qualified healthcare professional for medical advice, '
            'diagnosis, or treatment. Do not make health decisions based solely on this report.',
            disclaimer_style
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()