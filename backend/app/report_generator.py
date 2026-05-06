"""
Enhanced PDF report generator.
Uses only ASCII-safe characters to avoid black-box rendering in ReportLab's
default Helvetica font (which does not support Unicode beyond Latin-1).
CO2e is written as "CO2e", subscript 2 is avoided.
"""
import io
from datetime import datetime
from typing import Optional, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import CompanyDetails, ExtractedData, EmissionResult

PRIMARY     = colors.HexColor("#1a7f5a")
LIGHT_GREEN = colors.HexColor("#e8f8f0")
DARK_GRAY   = colors.HexColor("#2c3e50")
MID_GRAY    = colors.HexColor("#7f8c8d")
LIGHT_GRAY  = colors.HexColor("#f5f5f5")


def _safe(text: str) -> str:
    """Replace common Unicode symbols with ASCII equivalents safe for Helvetica."""
    return (
        text
        .replace("\u2082", "2")       # subscript 2  → 2
        .replace("\u00b2", "2")       # superscript 2 → 2
        .replace("\u2019", "'")       # right single quote
        .replace("\u2018", "'")       # left single quote
        .replace("\u201c", '"')       # left double quote
        .replace("\u201d", '"')       # right double quote
        .replace("\u2013", "-")       # en dash
        .replace("\u2014", "--")      # em dash
        .replace("\u2022", "*")       # bullet
        .replace("\u25a0", "*")       # filled square (used in recs)
        .replace("\u00b0", " deg")    # degree sign
        .replace("\u00e9", "e")       # e acute
        .replace("\u00e8", "e")
        .replace("\u00e0", "a")
        .replace("\u00fc", "u")
        .replace("\u00f6", "o")
        .replace("\u00e4", "a")
    )


def generate_pdf_report(
    company: CompanyDetails,
    extracted: ExtractedData,
    emissions: EmissionResult,
    esg_data: Optional[dict] = None,
    recommendations: Optional[List[dict]] = None,
    forecast: Optional[dict] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    title_style   = ParagraphStyle("T", parent=styles["Title"],   fontSize=24, textColor=PRIMARY,   spaceAfter=4,  alignment=TA_LEFT)
    sub_style     = ParagraphStyle("S", parent=styles["Normal"],  fontSize=11, textColor=MID_GRAY,  spaceAfter=2)
    section_style = ParagraphStyle("H", parent=styles["Heading2"],fontSize=12, textColor=PRIMARY,   spaceBefore=14, spaceAfter=5)
    body_style    = ParagraphStyle("B", parent=styles["Normal"],  fontSize=9,  textColor=DARK_GRAY, spaceAfter=3,  leading=13)
    note_style    = ParagraphStyle("N", parent=styles["Normal"],  fontSize=8,  textColor=MID_GRAY,  spaceAfter=3,  leading=12, leftIndent=8)
    footer_style  = ParagraphStyle("F", parent=styles["Normal"],  fontSize=7,  textColor=MID_GRAY,  alignment=TA_CENTER)

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Carbon Intelligence", title_style))
    story.append(Paragraph("Enterprise GHG Emissions and ESG Report", sub_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=10))

    # ── COMPANY ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Company Information", section_style))
    cd = [
        ["Company",          _safe(company.company_name)],
        ["Industry",         _safe(company.industry)],
        ["Reporting Period", _safe(company.reporting_period)],
    ]
    if company.contact_name:  cd.append(["Contact", _safe(company.contact_name)])
    if company.contact_email: cd.append(["Email",   _safe(company.contact_email)])
    ct = Table(cd, colWidths=[4.5*cm, 12.5*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1), LIGHT_GREEN), ("TEXTCOLOR",(0,0),(0,-1), PRIMARY),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, LIGHT_GRAY]),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),5),
    ]))
    story.append(ct)

    # ── ESG SCORE ────────────────────────────────────────────────────────────
    if esg_data:
        story.append(Paragraph("ESG Score and Rating", section_style))
        esg_color = colors.HexColor(esg_data.get("color", "#1a7f5a"))
        esg_rows = [
            ["ESG Score",         f"{esg_data['score']}/100"],
            ["Grade",             esg_data['grade']],
            ["Rating",            _safe(esg_data['label'])],
            ["Data Completeness", f"{esg_data['breakdown']['data_completeness']}%"],
            ["Confidence",        f"{esg_data['breakdown']['confidence']}%"],
            ["Emission Intensity",_safe(esg_data['breakdown']['emission_intensity'])],
        ]
        et = Table(esg_rows, colWidths=[5*cm, 12*cm])
        et.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,-1),LIGHT_GREEN), ("TEXTCOLOR",(0,0),(0,-1),PRIMARY),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, LIGHT_GRAY]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),5),
            ("TEXTCOLOR",(1,0),(1,0), esg_color), ("FONTNAME",(1,0),(1,0),"Helvetica-Bold"),
        ]))
        story.append(et)

    # ── EMISSIONS SUMMARY ────────────────────────────────────────────────────
    story.append(Paragraph("Emissions Summary", section_style))
    total_t = emissions.total_kg_co2e / 1000
    sd = [
        ["Metric",                       "Value"],
        ["Total Emissions",              f"{emissions.total_kg_co2e:,.2f} kg CO2e  ({total_t:.3f} tonnes)"],
        ["Scope 1 - Direct Combustion",  f"{emissions.scope1_kg_co2e:,.2f} kg CO2e"],
        ["Scope 2 - Electricity",        f"{emissions.scope2_kg_co2e:,.2f} kg CO2e"],
        ["Scope 3 - Indirect",           f"{emissions.scope3_kg_co2e:,.2f} kg CO2e"],
        ["Confidence Score",             f"{int(emissions.confidence_score*100)}%"],
    ]
    st = Table(sd, colWidths=[8*cm, 9*cm])
    st.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PRIMARY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT_GRAY]),
        ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#d4edda")),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),6),
    ]))
    story.append(st)

    # ── BREAKDOWN ────────────────────────────────────────────────────────────
    if emissions.breakdown:
        story.append(Paragraph("Emissions Breakdown", section_style))
        bd = [["Category", "Quantity", "Unit", "Factor", "kg CO2e"]]
        for item in emissions.breakdown:
            bd.append([
                _safe(item.get("category", "")),
                f"{item.get('quantity', 0):,.2f}",
                _safe(item.get("unit", "")),
                f"{item.get('emission_factor', 0):.4f}",
                f"{item.get('kg_co2e', 0):,.3f}",
            ])
        bt = Table(bd, colWidths=[6.5*cm, 2.5*cm, 2*cm, 2.5*cm, 3.5*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DARK_GRAY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT_GRAY]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),5),
            ("ALIGN",(1,0),(-1,-1),"RIGHT"),
        ]))
        story.append(bt)

    # ── RECOMMENDATIONS ──────────────────────────────────────────────────────
    if recommendations:
        story.append(Paragraph("Revenue and Efficiency Opportunities", section_style))
        priority_colors = {"high": "#e74c3c", "medium": "#f39c12", "low": "#7f8c8d"}
        for rec in recommendations[:5]:
            hex_color = priority_colors.get(rec.get("priority", "low"), "#7f8c8d")
            title = _safe(rec.get("title", ""))
            action = _safe(rec.get("action", ""))
            impact = _safe(rec.get("impact", ""))
            revenue = _safe(rec.get("revenue_impact", ""))
            story.append(Paragraph(
                f'<font color="{hex_color}">*</font> <b>{title}</b>',
                body_style
            ))
            if revenue:
                story.append(Paragraph(f"  Estimated Benefit: {revenue}", note_style))
            story.append(Paragraph(f"  Action: {action}", note_style))
            story.append(Paragraph(f"  Impact: {impact}", note_style))
            story.append(Spacer(1, 5))

    # ── FORECAST ─────────────────────────────────────────────────────────────
    if forecast and forecast.get("yearly_summary"):
        story.append(Paragraph("12-Month Emission Forecast", section_style))
        ys = forecast["yearly_summary"]
        optimized_total = ys['bau_total_kg'] - ys['optimized_saving_kg']
        fd = [
            ["Scenario",             "Annual Total (kg CO2e)", "Tonnes CO2e"],
            ["Business as Usual",    f"{ys['bau_total_kg']:,.0f}",    f"{ys['bau_total_tonnes']:.2f}"],
            ["Optimized Operations", f"{optimized_total:,.0f}",       f"{optimized_total/1000:.2f}"],
            ["Potential Saving",     f"{ys['optimized_saving_kg']:,.0f}", f"{ys['optimized_saving_kg']/1000:.2f}"],
        ]
        ft = Table(fd, colWidths=[6*cm, 5.5*cm, 5.5*cm])
        ft.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),PRIMARY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT_GRAY]),
            ("BACKGROUND",(0,3),(-1,3),colors.HexColor("#d4edda")),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),5),
        ]))
        story.append(ft)

    # ── SOURCE DATA ──────────────────────────────────────────────────────────
    story.append(Paragraph("Source Document Data", section_style))
    src = []
    if extracted.vendor_name:    src.append(["Vendor",      _safe(extracted.vendor_name)])
    if extracted.invoice_number: src.append(["Invoice #",   _safe(extracted.invoice_number)])
    if extracted.invoice_date:   src.append(["Date",        _safe(extracted.invoice_date)])
    if extracted.total_amount:   src.append(["Amount",      f"{extracted.total_amount:,.2f} {extracted.currency or ''}"])
    if extracted.energy_kwh:     src.append(["Electricity", f"{extracted.energy_kwh:,.2f} kWh"])
    if extracted.fuel_liters:    src.append(["Fuel",        f"{extracted.fuel_liters:,.2f} L ({_safe(extracted.fuel_type or 'unknown')})"])
    if extracted.distance_km:    src.append(["Distance",    f"{extracted.distance_km:,.2f} km ({_safe(extracted.transport_mode or 'unknown')})"])
    if extracted.waste_kg:       src.append(["Waste",       f"{extracted.waste_kg:,.2f} kg"])
    if extracted.source_filename:src.append(["Source File", _safe(extracted.source_filename)])

    if src:
        srt = Table(src, colWidths=[4.5*cm, 12.5*cm])
        srt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,-1),LIGHT_GREEN), ("TEXTCOLOR",(0,0),(0,-1),PRIMARY),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, LIGHT_GRAY]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dddddd")), ("PADDING",(0,0),(-1,-1),5),
        ]))
        story.append(srt)

    # ── METHODOLOGY ──────────────────────────────────────────────────────────
    story.append(Paragraph("Methodology and Notes", section_style))
    story.append(Paragraph(_safe(emissions.methodology_notes), note_style))
    if company.additional_notes:
        story.append(Paragraph(f"Additional Notes: {_safe(company.additional_notes)}", note_style))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Carbon Intelligence v2 -- Enterprise GHG and ESG Platform | "
        "Emissions calculated using IPCC/EPA/DEFRA factors | "
        "This report should be reviewed by a qualified sustainability professional.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
