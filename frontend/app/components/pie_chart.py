"""Camembert (pie chart) réel dessiné avec flet.canvas.Arc, puisque cette
version de Flet (0.85.3) ne fournit pas de contrôle PieChart natif."""
import math
import flet as ft
import flet.canvas as cv


def build_pie_chart(data: list[tuple[str, float, str]], size: int = 200) -> ft.Control:
    """data: liste de tuples (libellé, valeur, couleur_hex).
    Retourne un contrôle Canvas dessinant un camembert proportionnel, ou un
    cercle neutre si toutes les valeurs sont nulles."""
    total = sum(v for _, v, _ in data)
    radius = size / 2
    center = size / 2

    shapes = []
    if total <= 0:
        shapes.append(cv.Circle(center, center, radius - 5, paint=ft.Paint(color="#22392c", style=ft.PaintingStyle.FILL)))
    else:
        start_angle = -math.pi / 2  # démarre en haut (12h), sens horaire
        for _, value, color in data:
            if value <= 0:
                continue
            sweep = (value / total) * 2 * math.pi
            shapes.append(cv.Arc(
                x=5, y=5, width=size - 10, height=size - 10,
                start_angle=start_angle, sweep_angle=sweep, use_center=True,
                paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL),
            ))
            start_angle += sweep
        # Anneau central (effet "donut") pour améliorer la lisibilité
        shapes.append(cv.Circle(center, center, radius * 0.45, paint=ft.Paint(color="#182a20", style=ft.PaintingStyle.FILL)))

    return ft.Container(
        content=cv.Canvas(shapes=shapes, width=size, height=size),
        width=size, height=size,
    )


def build_pie_legend(data: list[tuple[str, float, str]]) -> ft.Control:
    total = sum(v for _, v, _ in data) or 1
    rows = []
    for label, value, color in data:
        pct = (value / total * 100) if total else 0
        rows.append(ft.Row([
            ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
            ft.Text(label, size=13, color="#e8f0ea", expand=True),
            ft.Text(f"{value:.0f} ({pct:.0f}%)", size=13, color="#9db3a4"),
        ], spacing=10))
    return ft.Column(rows, spacing=10)
