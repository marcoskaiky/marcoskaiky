"""Desenha o calendario de contribuicoes como SVG animado.

Grade classica de 53 semanas x 7 dias, caixas arredondadas, rampa verde
parecida com a do GitHub. A revelacao e uma varredura diagonal (o atraso de
cada celula e proporcional a `coluna + linha`), feita com keyframes CSS que
rodam no load e congelam -- sem brilho em loop.

Saida: contrib-heatmap.svg
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from xml.sax.saxutils import escape

from config import ACCENT, BG, BORDER, DATA, DIM, FG, HEAT_PALETTE, MONO, ROOT

SRC = DATA / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

COLS, ROWS = 53, 7
CELL, GAP = 12.0, 3.0
PITCH = CELL + GAP
PAD = 16.0
LEFT = 34.0
MONTH_H = 18.0

GRID_X = PAD + LEFT
GRID_Y = PAD + MONTH_H
GRID_W = COLS * PITCH - GAP
GRID_H = ROWS * PITCH - GAP

WIDTH = GRID_X + GRID_W + PAD
HEIGHT = 234.0

STEP = 0.016     # atraso por diagonal
DUR = 0.50

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = {1: "Mon", 3: "Wed", 5: "Fri"}


def sunday_index(d: date) -> int:
    return (d.weekday() + 1) % 7


def pretty(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}"


def load() -> dict:
    if not SRC.exists():
        raise SystemExit("data/contributions.json nao existe -- rode fetch_contributions.py antes")
    return json.loads(SRC.read_text(encoding="utf-8"))


def neon_threshold(days: list[dict]) -> int:
    """Corte para o nivel 5: os ~5% melhores dias ativos ganham o tom neon."""
    active = sorted(d["count"] for d in days if d["count"] > 0)
    if len(active) < 20:
        return 10 ** 9
    return active[int(len(active) * 0.95)]


def build_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload["stats"]
    cutoff = neon_threshold(days)

    first = date.fromisoformat(days[0]["date"])
    origin = first - timedelta(days=sunday_index(first))

    cells: list[str] = []
    month_labels: list[str] = []
    seen_months: set[int] = set()
    max_diag = 0

    for day in days:
        d = date.fromisoformat(day["date"])
        col = (d - origin).days // 7
        row = sunday_index(d)
        if not (0 <= col < COLS):
            continue

        level = int(day["level"])
        if level >= 4 and day["count"] >= cutoff:
            level = 5

        x = GRID_X + col * PITCH
        y = GRID_Y + row * PITCH
        diag = col + row
        max_diag = max(max_diag, diag)

        plural = "" if day["count"] == 1 else "s"
        cells.append(
            f'<rect class="c d{diag}" x="{x:.1f}" y="{y:.1f}" width="{CELL:.0f}" '
            f'height="{CELL:.0f}" rx="2.5" fill="{HEAT_PALETTE[level]}">'
            f'<title>{day["count"]} contribution{plural} on {escape(pretty(d))}</title>'
            f"</rect>"
        )

        # rotula a coluna onde um mes comeca (dia 1..7, uma vez por mes)
        if d.day <= 7 and d.month not in seen_months and col < COLS - 2:
            seen_months.add(d.month)
            month_labels.append(
                f'<text x="{x:.1f}" y="{PAD + 10:.1f}">{MONTHS[d.month - 1]}</text>'
            )

    weekdays = "".join(
        f'<text x="{PAD + LEFT - 8:.1f}" y="{GRID_Y + r * PITCH + CELL - 2:.1f}" '
        f'text-anchor="end">{label}</text>'
        for r, label in WEEKDAYS.items()
    )

    legend_y = GRID_Y + GRID_H + 20
    legend_x = WIDTH - PAD - 6 * 14 - 62
    legend = (
        f'<text x="{legend_x - 6:.1f}" y="{legend_y + 9:.1f}" text-anchor="end">Less</text>'
        + "".join(
            f'<rect x="{legend_x + i * 14:.1f}" y="{legend_y:.1f}" width="11" '
            f'height="11" rx="2.5" fill="{c}"/>'
            for i, c in enumerate(HEAT_PALETTE)
        )
        + f'<text x="{legend_x + 6 * 14 + 4:.1f}" y="{legend_y + 9:.1f}">More</text>'
    )

    current = stats["current_streak"]["length"]
    longest = stats["longest_streak"]["length"]
    best = stats["best_day"]
    footer_bits = [
        f"current streak {current}d",
        f"longest {longest}d",
        f"best day {best['count']} on {pretty(date.fromisoformat(best['date']))}",
        f"{stats['active_days']}/{stats['tracked_days']} active days",
    ]

    rule_y = legend_y + 26
    delays = "".join(f".d{i}{{animation-delay:{i * STEP:.3f}s}}" for i in range(max_diag + 1))
    tail = (max_diag * STEP) + DUR

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH:.0f}" height="{HEIGHT:.0f}" viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" role="img" aria-label="{escape(payload['total_label'])}">
<style>
text{{font-family:{MONO};font-size:10px;fill:{DIM}}}
.c{{opacity:0;transform-box:fill-box;transform-origin:50% 50%;animation:pop {DUR:.2f}s cubic-bezier(.2,.7,.3,1) forwards}}
@keyframes pop{{from{{opacity:0;transform:translate(-6px,-6px) scale(.35)}}to{{opacity:1;transform:none}}}}
.late{{opacity:0;animation:fade .6s ease-out {tail:.2f}s forwards}}
@keyframes fade{{to{{opacity:1}}}}
{delays}
</style>
<rect width="100%" height="100%" rx="8" fill="{BG}" stroke="{BORDER}"/>
<g class="late">{"".join(month_labels)}{weekdays}</g>
{"".join(cells)}
<g class="late">
{legend}
<line x1="{PAD:.1f}" y1="{rule_y:.1f}" x2="{WIDTH - PAD:.1f}" y2="{rule_y:.1f}" stroke="{BORDER}"/>
<text x="{PAD:.1f}" y="{rule_y + 22:.1f}" fill="{ACCENT}" font-size="14">{escape(payload['total_label'])}</text>
<text x="{PAD:.1f}" y="{rule_y + 40:.1f}" fill="{DIM}">{escape(" · ".join(footer_bits))}</text>
<text x="{WIDTH - PAD:.1f}" y="{rule_y + 40:.1f}" text-anchor="end" fill="{FG}" opacity="0.55">updated {payload['generated_at'][:10]}</text>
</g>
</svg>
"""


def main() -> None:
    payload = load()
    # newline="\n" para o arquivo sair identico no Windows e no runner Linux
    OUT.write_text(build_svg(payload), encoding="utf-8", newline="\n")
    print(f"  -> {OUT.name}  ({WIDTH:.0f}x{HEIGHT:.0f}, {payload['total_label']})")


if __name__ == "__main__":
    main()
