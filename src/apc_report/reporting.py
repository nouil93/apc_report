"""Reporting helpers for charts and PDF generation."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import datetime as dt

import cairosvg
import pandas as pd
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import DeviceConfig


def generate_plotly_svg(df: pd.DataFrame, device_name: str) -> bytes:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=df["timestamp"], y=df["temp_ambient_c"], mode="lines", name="Ambient °C"))
    figure.add_trace(go.Scatter(x=df["timestamp"], y=df["temp_ups_c"], mode="lines", name="UPS °C"))
    figure.update_layout(
        title=f"Temperature history - {device_name}",
        xaxis_title="Timestamp",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        legend_title="Metrics",
    )
    return figure.to_image(format="svg")


def export_csv(df: pd.DataFrame, output_dir: Path, device_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{device_name}_telemetry.csv"
    df.to_csv(path, index=False)
    return path


def generate_pdf_report(
    df: pd.DataFrame,
    daily_summary: pd.DataFrame,
    svg_data: bytes,
    output_dir: Path,
    device: DeviceConfig,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().strftime("%Y-%m-%d")
    report_path = output_dir / f"{device.name}_report_{today}.pdf"

    document = SimpleDocTemplate(str(report_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"APC report - {device.name}", styles["Heading1"]))
    story.append(Paragraph(f"Generated on {today}", styles["Normal"]))
    story.append(Spacer(1, 12))

    summary_table_data = [daily_summary.columns.tolist()] + daily_summary.astype(str).values.tolist()
    summary_table = Table(summary_table_data)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#23395B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6FA")]),
            ]
        )
    )
    story.append(Paragraph("Daily min/max summary", styles["Heading2"]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    png_data = cairosvg.svg2png(bytestring=svg_data)
    story.append(Image(BytesIO(png_data), width=520, height=260))
    story.append(Spacer(1, 12))

    metadata = [
        ["Metric", "Value"],
        ["Rows collected", str(len(df))],
        ["First timestamp", str(df["timestamp"].min())],
        ["Last timestamp", str(df["timestamp"].max())],
    ]
    metadata_table = Table(metadata)
    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#23395B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6FA")]),
            ]
        )
    )
    story.append(Paragraph("Collection metadata", styles["Heading2"]))
    story.append(metadata_table)

    document.build(story)
    return report_path
