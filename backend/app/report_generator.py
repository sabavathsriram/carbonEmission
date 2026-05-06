"""
PDF report generator for Carbon Intelligence.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import CompanyDetails, ExtractedData, EmissionResult

# Brand colors
PRIMARY = colors.HexColor("#1a7f5a")
SECONDARY = colors.HexColor("#2ecc71")
LIGHT_GREEN = colors.HexColor("#e8f8f0")
DARK_GRAY = colors.HexColor("#2c3e50")
MID_GRAY = colors.HexColor("#7f8c8d")
LIGHT_GRAY = colors.HexColor("#f5f5f5")


def generate_pdf_report(
    company: CompanyDetails,
    extracted: ExtractedData,
    emissions: EmissionResult,
) -> bytes:
    """Generate a PDF report and return as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Custom styles ---
    title_style = ParagraphStyle(
        "CITitle",
        parent=styles["Title"],
        fontSize=26,
        textColor=PRIMARY,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "CISubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=MID_GRAY,
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "CISection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "CIBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=4,
        leading=14,
    )
    note_style = ParagraphStyle(
        "CINote",
        parent=styles["Normal"],
        fontSize=9,
        textColor=MID_GRAY,
        spaceAfter=4,
        leading=13,
        leftIndent=10,
    )

    # ---- HEADER ----
    story.append(Paragraph("Carbon Intelligence", title_style))
    story.append(Paragraph("GHG Emissions Report", subtitle_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=12))

    # ---- COMPANY DETAILS ----
    story.append(Paragraph("Company Information", section_style))
    company_data = [
        ["Company Name", company.company_name],
        ["Industry", company.industry],
        ["Reporting Period", company.reporting_period],
    ]
    if company.contact_name:
        company_data.append(["Contact", company.contact_name])
    if company.contact_email:
        company_data.append(["Email", company.contact_email])

    company_table = Table(company_data, colWidths=[5 * cm, 12 * cm])
    company_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(company_table)

    # ---- EMISSIONS SUMMARY ----
    story.append(Paragraph("Emissions Summary", section_style))

    confidence_pct = f"{int(emissions.confidence_score * 100)}%"
    total_tonnes = emissions.total_kg_co2e / 1000

    summary_data = [
        ["Metric", "Value"],
        ["Total Emissions", f"{emissions.total_kg_co2e:,.2f} kg CO₂e  ({total_tonnes:.3f} tonnes)"],
        ["Scope 1 (Direct)", f"{emissions.scope1_kg_co2e:,.2f} kg CO₂e"],
        ["Scope 2 (Electricity)", f"{emissions.scope2_kg_co2e:,.2f} kg CO₂e"],
        ["Scope 3 (Indirect)", f"{emissions.scope3_kg_co2e:,.2f} kg CO₂e"],
        ["Confidence Score", confidence_pct],
    ]

    summary_table = Table(summary_data, colWidths=[7 * cm, 10 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#d4edda")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)

    # ---- BREAKDOWN ----
    if emissions.breakdown:
        story.append(Paragraph("Emissions Breakdown", section_style))
        breakdown_data = [["Category", "Quantity", "Unit", "Factor", "kg CO₂e"]]
        for item in emissions.breakdown:
            breakdown_data.append([
                item.get("category", ""),
                f"{item.get('quantity', 0):,.2f}",
                item.get("unit", ""),
                f"{item.get('emission_factor', 0):.4f}",
                f"{item.get('kg_co2e', 0):,.3f}",
            ])

        breakdown_table = Table(
            breakdown_data,
            colWidths=[6.5 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 3.5 * cm]
        )
        breakdown_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_GRAY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(breakdown_table)

    # ---- EXTRACTED DATA ----
    story.append(Paragraph("Source Document Data", section_style))
    source_rows = []
    if extracted.vendor_name:
        source_rows.append(["Vendor", extracted.vendor_name])
    if extracted.invoice_number:
        source_rows.append(["Invoice #", extracted.invoice_number])
    if extracted.invoice_date:
        source_rows.append(["Date", extracted.invoice_date])
    if extracted.total_amount:
        source_rows.append(["Total Amount", f"{extracted.total_amount:,.2f} {extracted.currency or ''}"])
    if extracted.energy_kwh:
        source_rows.append(["Electricity", f"{extracted.energy_kwh:,.2f} kWh"])
    if extracted.fuel_liters:
        source_rows.append(["Fuel", f"{extracted.fuel_liters:,.2f} L ({extracted.fuel_type or 'unknown'})"])
    if extracted.distance_km:
        source_rows.append(["Distance", f"{extracted.distance_km:,.2f} km ({extracted.transport_mode or 'unknown'})"])
    if extracted.waste_kg:
        source_rows.append(["Waste", f"{extracted.waste_kg:,.2f} kg"])

    if source_rows:
        source_table = Table(source_rows, colWidths=[5 * cm, 12 * cm])
        source_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN),
            ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(source_table)
    else:
        story.append(Paragraph("No structured source data extracted.", body_style))

    # ---- METHODOLOGY ----
    story.append(Paragraph("Methodology & Notes", section_style))
    story.append(Paragraph(emissions.methodology_notes, note_style))
    if company.additional_notes:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Additional Notes: {company.additional_notes}", note_style))

    # ---- FOOTER ----
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Spacer(1, 6))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=MID_GRAY, alignment=TA_CENTER
    )
    story.append(Paragraph(
        "Carbon Intelligence — Automated GHG Emissions Report | "
        "This report is generated using standard emission factors and should be reviewed by a qualified professional.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
