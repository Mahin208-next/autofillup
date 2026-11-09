"""
Export engine for SurveyForge AI.
Handles CSV, multi-sheet Excel, SPSS (.sav) via pyreadstat, and PDF reports via reportlab.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import io
import pandas as pd
from config import ETHICAL_PROVENANCE_TAG, DEFAULT_DISCLAIMER, EXPORT_DIR


class ExportEngine:
    """Manages multi-format export workflows with strict academic synthetic provenance."""

    @staticmethod
    def export_csv(df: pd.DataFrame, output_path: Optional[Path] = None) -> bytes:
        """Export dataset to CSV with top disclaimer comment block."""
        buffer = io.StringIO()
        buffer.write(f"# {DEFAULT_DISCLAIMER}\n")
        buffer.write(f"# Provenance: data_type='{ETHICAL_PROVENANCE_TAG}'\n")
        df.to_csv(buffer, index=False)

        csv_bytes = buffer.getvalue().encode("utf-8")
        if output_path:
            with open(output_path, "wb") as f:
                f.write(csv_bytes)
        return csv_bytes

    @staticmethod
    def export_excel(
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        validation_summary: Optional[Dict[str, Any]] = None,
        questions: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[Path] = None
    ) -> bytes:
        """Export multi-sheet Excel workbook: Data, Metadata, Validation, Codebook."""
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            # Sheet 1: Synthetic Data
            df.to_excel(writer, sheet_name="Synthetic Data", index=False)

            # Sheet 2: Metadata & Assumptions
            meta_rows = [
                {"Parameter": "Ethical Notice", "Value": DEFAULT_DISCLAIMER},
                {"Parameter": "Data Type", "Value": ETHICAL_PROVENANCE_TAG},
                {"Parameter": "Total Records", "Value": len(df)},
                {"Parameter": "Total Variables", "Value": len(df.columns)},
                {"Parameter": "Random Seed", "Value": metadata.get("random_seed", 42)},
                {"Parameter": "Generation Mode", "Value": metadata.get("generation_mode", "statistical")},
                {"Parameter": "Simulation Scenario", "Value": metadata.get("scenario", "Baseline")},
                {"Parameter": "Timestamp", "Value": metadata.get("timestamp", "")}
            ]
            pd.DataFrame(meta_rows).to_excel(writer, sheet_name="Metadata & Assumptions", index=False)

            # Sheet 3: Validation Summary
            if validation_summary:
                val_rows = [{"Metric": k, "Value": str(v)} for k, v in validation_summary.items()]
                pd.DataFrame(val_rows).to_excel(writer, sheet_name="Validation Summary", index=False)

            # Sheet 4: Codebook & Questions
            if questions:
                codebook_rows = []
                for q in questions:
                    codebook_rows.append({
                        "Variable Name": q.get("variable_name"),
                        "Question ID": q.get("question_id"),
                        "Question Text": q.get("question_text"),
                        "Question Type": q.get("question_type"),
                        "Category": q.get("category"),
                        "Required": q.get("required"),
                        "Reverse Coded": q.get("reverse_coded"),
                        "Answer Options": ", ".join(q.get("answer_options", []))
                    })
                pd.DataFrame(codebook_rows).to_excel(writer, sheet_name="Survey Codebook", index=False)

        excel_bytes = buffer.getvalue()
        if output_path:
            with open(output_path, "wb") as f:
                f.write(excel_bytes)
        return excel_bytes

    @staticmethod
    def export_spss(df: pd.DataFrame, output_path: Path) -> bool:
        """Export SPSS .sav file using pyreadstat."""
        try:
            import pyreadstat

            # Prepare dataframe: shorten column names if needed (>64 chars not allowed in SPSS)
            export_df = df.copy()
            rename_map = {}
            for col in export_df.columns:
                clean_name = str(col)[:60].replace(" ", "_").replace("-", "_")
                rename_map[col] = clean_name
            export_df = export_df.rename(columns=rename_map)

            # Column labels
            column_labels = {rename_map[col]: f"Synthetic Var: {col}" for col in df.columns}

            pyreadstat.write_sav(
                export_df,
                str(output_path),
                file_label="SurveyForge Synthetic Dataset",
                column_labels=column_labels
            )
            return True
        except Exception as e:
            print(f"SPSS export error: {e}")
            return False

    @staticmethod
    def export_pdf_report(
        project_name: str,
        df: pd.DataFrame,
        analysis_summary: List[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> bytes:
        """Generate PDF statistical summary report using reportlab."""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#991b1b"),
            backColor=colors.HexColor("#fee2e2"),
            borderColor=colors.HexColor("#fca5a5"),
            borderWidth=1,
            borderPadding=6,
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            "H2Style",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6
        )

        elements = []

        # Title
        elements.append(Paragraph(f"SurveyForge AI — Statistical Simulation Report", title_style))
        elements.append(Paragraph(f"Project: {project_name}", subtitle_style))

        # Ethical Notice
        elements.append(Paragraph(f"<b>ETHICAL PROVENANCE NOTICE:</b> {DEFAULT_DISCLAIMER}", disclaimer_style))

        # Dataset Overview
        elements.append(Paragraph("1. Dataset Overview", h2_style))
        overview_data = [
            ["Metric", "Value"],
            ["Total Synthetic Records", str(len(df))],
            ["Total Variables", str(len(df.columns))],
            ["Provenance Label", ETHICAL_PROVENANCE_TAG],
            ["Survey Population Target", "Adults aged 18+ in Bangladesh"]
        ]
        t1 = Table(overview_data, colWidths=[200, 300])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0, 0), (-1, -1), 8)
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 14))

        # Statistical Analysis Findings
        elements.append(Paragraph("2. Statistical Analysis Summary", h2_style))
        if analysis_summary:
            stat_table_data = [["Analysis / Test", "Statistic", "p-value", "Interpretation"]]
            for item in analysis_summary[:8]:
                tname = str(item.get("test_name", ""))[:28]
                stat_val = f"{item.get('test_statistic'):.3f}" if item.get('test_statistic') is not None else "N/A"
                pval_val = f"{item.get('p_value'):.4f}" if item.get('p_value') is not None else "N/A"
                interp = str(item.get("interpretation", ""))[:55] + "..."
                stat_table_data.append([tname, stat_val, pval_val, interp])

            t2 = Table(stat_table_data, colWidths=[130, 60, 60, 250])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('FONTSIZE', (0, 0), (-1, -1), 8)
            ]))
            elements.append(t2)
        else:
            elements.append(Paragraph("No statistical tests recorded yet for this project.", body_style))

        elements.append(Spacer(1, 14))

        # Simulation Assumptions & Methodological Transparency
        elements.append(Paragraph("3. Methodology & Simulation Limitations", h2_style))
        meth_text = (
            "This synthetic dataset was generated using a controlled multivariate Gaussian copula "
            "sampling framework with user-configured latent factors and categorical probability distributions. "
            "Findings in this report must be used exclusively for testing software, modeling pipelines, "
            "and practicing statistical methods. They must not be cited as empirical population claims."
        )
        elements.append(Paragraph(meth_text, body_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        return pdf_bytes
