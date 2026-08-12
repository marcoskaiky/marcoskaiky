"""Monta a mao o cartao no estilo `neofetch`.

Barra de titulo + linhas chave/valor coloridas. O conteudo mora em
config.INFO_ROWS -- de proposito ele NAO repete estatisticas do GitHub: o
heatmap ja cobre os numeros, entao o cartao fica com a historia que os
numeros nao contam.

Cada linha surge com um escalonamento curto, para o painel parecer que esta
sendo impresso ao lado do retrato. `STATIC=1` emite um quadro congelado, util
para preview local.

Saida: info-card.svg
"""

from __future__ import annotations

import os
from xml.sax.saxutils import escape

from config import (
    ACCENT, ACCENT_2, BG, BORDER, DIM, FG, INFO_ROWS, MONO, PROMPT, ROOT,
)

OUT = ROOT / "info-card.svg"

STATIC = os.environ.get("STATIC") == "1"

WIDTH = 560.0
PAD = 18.0
FONT_SIZE = 12.5
CHAR_W = 7.05
KEY_COLS = 11          # largura da coluna de chave, preenchida com pontos
VALUE_COL = KEY_COLS + 2

TITLEBAR_H = 34.0
ROW_H = 24.0
SEP_H = 14.0
GAP = 12.0
SWATCH_H = 12.0

STAGGER = 0.07
FADE = 0.45

PALETTE_BLOCKS = ["#f85149", "#d29922", "#3fb950", "#58a6ff", "#bc8cff", "#39c5cf"]


def layout() -> tuple[list[tuple], float]:
    """Calcula o y de cada linha e a altura total do cartao."""
    placed: list[tuple] = []
    y = TITLEBAR_H + GAP
    for key, value in INFO_ROWS:
        if key == "---":
            placed.append(("sep", y + SEP_H / 2, "", ""))
            y += SEP_H
        else:
            placed.append(("row", y + ROW_H - 7, key, value))
            y += ROW_H
    height = y + GAP + SWATCH_H + PAD
    return placed, height


def build_svg() -> str:
    placed, height = layout()
    x_value = PAD + VALUE_COL * CHAR_W

    css_rows = "" if STATIC else (
        ".ln{opacity:0;animation:in %.2fs ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}"
        "to{opacity:1;transform:none}}" % FADE
    )
    delays = "" if STATIC else "".join(
        ".s%d{animation-delay:%.2fs}" % (i, i * STAGGER) for i in range(len(placed))
    )

    body: list[str] = []
    for i, (kind, y, key, value) in enumerate(placed):
        cls = "" if STATIC else f' class="ln s{i}"'
        if kind == "sep":
            body.append(
                f'<line{cls} x1="{PAD:.1f}" y1="{y:.1f}" x2="{WIDTH - PAD:.1f}" '
                f'y2="{y:.1f}" stroke="{BORDER}" stroke-width="1"/>'
            )
            continue

        label = f"{key}{'.' * max(0, KEY_COLS - len(key))}:" if key else ""
        body.append(
            f'<g{cls}>'
            f'<text x="{PAD:.1f}" y="{y:.1f}" fill="{ACCENT_2}" '
            f'xml:space="preserve">{escape(label)}</text>'
            f'<text x="{x_value:.1f}" y="{y:.1f}" fill="{FG}" '
            f'xml:space="preserve">{escape(value)}</text>'
            f"</g>"
        )

    swatch_y = height - PAD - SWATCH_H
    swatches = "".join(
        f'<rect x="{PAD + i * (SWATCH_H * 2 + 4):.1f}" y="{swatch_y:.1f}" '
        f'width="{SWATCH_H * 2:.1f}" height="{SWATCH_H:.1f}" rx="2" fill="{c}"/>'
        for i, c in enumerate(PALETTE_BLOCKS)
    )

    dots = "".join(
        f'<circle cx="{PAD + 6 + i * 16:.1f}" cy="{TITLEBAR_H / 2:.1f}" r="5" fill="{c}"/>'
        for i, c in enumerate(("#f85149", "#d29922", "#3fb950"))
    )

    nl = "\n"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH:.0f}" height="{height:.0f}" viewBox="0 0 {WIDTH:.0f} {height:.0f}" role="img" aria-label="Cartao de perfil no estilo neofetch">
<style>
text{{font-family:{MONO};font-size:{FONT_SIZE:.1f}px}}
{css_rows}{delays}
</style>
<rect width="100%" height="100%" rx="8" fill="{BG}" stroke="{BORDER}"/>
<path d="M0 8a8 8 0 0 1 8-8h{WIDTH - 16:.0f}a8 8 0 0 1 8 8v{TITLEBAR_H - 8:.0f}H0z" fill="#161b22"/>
<line x1="0" y1="{TITLEBAR_H:.1f}" x2="{WIDTH:.0f}" y2="{TITLEBAR_H:.1f}" stroke="{BORDER}"/>
{dots}
<text x="{WIDTH / 2:.1f}" y="{TITLEBAR_H / 2 + 4.5:.1f}" text-anchor="middle" fill="{DIM}">{escape(PROMPT)} -- neofetch</text>
{nl.join(body)}
{swatches}
<text x="{WIDTH - PAD:.1f}" y="{swatch_y + SWATCH_H - 1:.1f}" text-anchor="end" fill="{ACCENT}" font-size="10.5">{escape(PROMPT)}</text>
</svg>
"""


def main() -> None:
    OUT.write_text(build_svg(), encoding="utf-8", newline="\n")
    _, height = layout()
    mode = "estatico" if STATIC else "animado"
    print(f"  -> {OUT.name}  ({WIDTH:.0f}x{height:.0f}, {mode})")


if __name__ == "__main__":
    main()
