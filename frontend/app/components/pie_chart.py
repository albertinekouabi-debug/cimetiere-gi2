"""Camembert (pie chart) réel dessiné avec flet.canvas.Arc, puisque cette
version de Flet (0.85.3) ne fournit pas de contrôle PieChart natif.

Conçu pour être robuste en priorité : disposition toujours empilée
(camembert au-dessus, légende en dessous), sans combinaison Row(wrap=True) +
Container(expand=True) — cette combinaison s'est révélée produire un
espace vide énorme et imprévisible sur certaines tailles d'écran."""
import math
import flet as ft
import flet.canvas as cv

MIN_LABEL_FRACTION = 0.06  # ne pas afficher de pourcentage sur une tranche trop fine (<6%) pour éviter le chevauchement de texte


def build_pie_chart(data: list[tuple[str, float, str]], size: int = 220) -> ft.Control:
    """data: liste de tuples (libellé, valeur, couleur_hex).
    Dessine un camembert en anneau (donut) avec le pourcentage affiché
    directement sur chaque tranche suffisamment grande, et le total au
    centre — pour une lecture immédiate sans avoir à croiser avec la
    légende."""
    total = sum(v for _, v, _ in data)
    radius = size / 2
    center = size / 2

    shapes = []
    if total <= 0:
        shapes.append(cv.Circle(center, center, radius - 5, paint=ft.Paint(color="#22392c", style=ft.PaintingStyle.FILL)))
        shapes.append(cv.Text(
            center, center, "Aucune\ndonnée",
            style=ft.TextStyle(size=13, color="#6b8577", weight=ft.FontWeight.BOLD),
            text_align=ft.TextAlign.CENTER, alignment=ft.Alignment.CENTER,
        ))
    else:
        start_angle = -math.pi / 2  # démarre en haut (12h), sens horaire
        label_radius = radius * 0.72  # position des labels : entre l'anneau intérieur et le bord
        for _, value, color in data:
            if value <= 0:
                continue
            fraction = value / total
            sweep = fraction * 2 * math.pi
            shapes.append(cv.Arc(
                x=5, y=5, width=size - 10, height=size - 10,
                start_angle=start_angle, sweep_angle=sweep, use_center=True,
                paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL),
            ))
            if fraction >= MIN_LABEL_FRACTION:
                mid_angle = start_angle + sweep / 2
                label_x = center + label_radius * math.cos(mid_angle)
                label_y = center + label_radius * math.sin(mid_angle)
                shapes.append(cv.Text(
                    label_x, label_y, f"{fraction * 100:.0f}%",
                    style=ft.TextStyle(size=13, color="#ffffff", weight=ft.FontWeight.BOLD),
                    text_align=ft.TextAlign.CENTER, alignment=ft.Alignment.CENTER,
                ))
            start_angle += sweep

        # Anneau central (effet "donut") avec le total inscrit au milieu.
        shapes.append(cv.Circle(center, center, radius * 0.48, paint=ft.Paint(color="#182a20", style=ft.PaintingStyle.FILL)))
        shapes.append(cv.Text(
            center, center - 8, f"{total:.0f}",
            style=ft.TextStyle(size=22, color="#e8f0ea", weight=ft.FontWeight.BOLD),
            text_align=ft.TextAlign.CENTER, alignment=ft.Alignment.CENTER,
        ))
        shapes.append(cv.Text(
            center, center + 14, "total",
            style=ft.TextStyle(size=11, color="#9db3a4"),
            text_align=ft.TextAlign.CENTER, alignment=ft.Alignment.CENTER,
        ))

    return ft.Container(
        content=cv.Canvas(shapes=shapes, width=size, height=size),
        width=size, height=size, alignment=ft.Alignment.CENTER,
    )


def build_pie_legend(data: list[tuple[str, float, str]]) -> ft.Control:
    """Légende sous forme de liste compacte : pastille de couleur, libellé,
    valeur brute et pourcentage — toujours en Column (jamais en Row élastique)
    pour un rendu stable sur toutes les largeurs d'écran."""
    total = sum(v for _, v, _ in data) or 1
    rows = []
    for label, value, color in data:
        pct = (value / total * 100) if total else 0
        rows.append(ft.Container(
            padding=ft.Padding(10, 8, 10, 8),
            border_radius=8,
            bgcolor="#182a20",
            content=ft.Row([
                ft.Container(width=12, height=12, bgcolor=color, border_radius=6),
                ft.Text(label, size=13, color="#e8f0ea", expand=True),
                ft.Text(f"{value:.0f}", size=13, color="#e8f0ea", weight=ft.FontWeight.BOLD),
                ft.Container(
                    padding=ft.Padding(8, 2, 8, 2), border_radius=10,
                    bgcolor="#22392c",
                    content=ft.Text(f"{pct:.0f}%", size=12, color="#9db3a4"),
                ),
            ], spacing=10, alignment=ft.MainAxisAlignment.START),
        ))
    return ft.Column(rows, spacing=8)


def build_pie_section(title: str, data: list[tuple[str, float, str]], page: ft.Page) -> ft.Control:
    """Assemble titre + camembert + légende dans une disposition toujours
    empilée (Column), volontairement simple et robuste plutôt qu'une mise en
    page côte-à-côte fragile sur petits écrans."""
    from app.components.theme import card_container, responsive_width

    chart_size = responsive_width(page, max=220, min=160)
    return card_container(ft.Column([
        ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color="#e8f0ea"),
        ft.Container(height=16),
        ft.Row([build_pie_chart(data, size=chart_size)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=16),
        build_pie_legend(data),
    ]))
