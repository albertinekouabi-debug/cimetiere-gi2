"""Génération de PDF (reçus de paiement, exports) avec ReportLab."""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

PRIMARY = colors.HexColor("#2d3a5e")
ACCENT = colors.HexColor("#2d9e8a")


def generate_recu_pdf(paiement) -> bytes:
    """Génère un reçu de paiement individuel (format A5-like sur A4)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=25 * mm, bottomMargin=20 * mm,
                             leftMargin=20 * mm, rightMargin=20 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], textColor=PRIMARY, alignment=TA_CENTER)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], alignment=TA_CENTER, textColor=colors.grey)

    elements = [
        Paragraph("Cimetière Municipal", title_style),
        Paragraph("Reçu de paiement", sub_style),
        Spacer(1, 10 * mm),
    ]

    concession = paiement.concession
    grave = concession.grave

    data = [
        ["N° de reçu", paiement.numero_recu],
        ["Date de paiement", paiement.date_paiement.strftime("%d/%m/%Y")],
        ["Famille", concession.famille_nom],
        ["Contact", concession.famille_contact or "—"],
        ["Caveau", grave.numero if grave else "—"],
        ["Mode de paiement", paiement.get_mode_paiement_display()],
        ["Montant", f"{paiement.montant:,.0f} FCFA".replace(",", " ")],
    ]
    table = Table(data, colWidths=[60 * mm, 90 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15 * mm))
    elements.append(Paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}. "
        "Ce reçu fait foi de paiement pour la concession funéraire mentionnée ci-dessus.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))
    doc.build(elements)
    return buf.getvalue()


def generate_paiements_export_pdf(paiements) -> bytes:
    """Génère un export PDF listant plusieurs paiements (tableau)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=12 * mm, rightMargin=12 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], textColor=PRIMARY)

    elements = [
        Paragraph("Export des paiements — Cimetière Municipal", title_style),
        Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]

    header = ["N° reçu", "Date", "Famille", "Caveau", "Mode", "Montant (FCFA)"]
    rows = [header]
    total = 0
    for p in paiements:
        rows.append([
            p.numero_recu, p.date_paiement.strftime("%d/%m/%Y"), p.concession.famille_nom[:30],
            p.concession.grave.numero if p.concession.grave else "—",
            p.get_mode_paiement_display(), f"{p.montant:,.0f}".replace(",", " "),
        ])
        total += float(p.montant)
    rows.append(["", "", "", "", "TOTAL", f"{total:,.0f}".replace(",", " ")])

    table = Table(rows, colWidths=[28 * mm, 22 * mm, 45 * mm, 25 * mm, 25 * mm, 30 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (5, 0), (5, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
