"""Converte a foto preparada num SVG ASCII que se digita sozinho.

A imagem e reduzida a uma grade de caracteres e o brilho de cada celula
escolhe um glifo da rampa de densidade. Duas escolhas mantem o resultado
limpo em vez de baguncado:

  * monocromatico -- uma unica cor de preenchimento. Colorir por caractere e
    exatamente o que faz a maioria dos retratos ASCII parecer estatica;
  * alto contraste -- o fundo cai no glifo espaco, entao so o sujeito imprime.

A animacao e SMIL: cada linha tem um clip horizontal que abre da esquerda
para a direita, escalonado de cima para baixo, com um bloco-cursor correndo
na borda. Roda uma vez e congela (fill="freeze") -- sem loop.

Saida: portrait-ascii.svg
"""

from __future__ import annotations

from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

from config import ASCII_COLS, ASCII_ROWS, ACCENT, BG, FG, MONO, RAMP, ROOT, ASSETS

PREPPED = ASSETS / "source-prepped.png"
OUT = ROOT / "portrait-ascii.svg"

FONT_SIZE = 12.0
CHAR_W = 7.2          # avanco fixo por caractere (travado com textLength)
LINE_H = 13.0
PAD = 10.0

# >1 clareia os meios-tons. Acima de ~1.2 o rosto comeca a esvaziar (olho e
# bochecha caem no glifo espaco), entao a margem util e estreita.
GAMMA = 1.1

LINE_DUR = 0.50       # duracao do sweep de uma linha
STAGGER = 0.045       # atraso entre linhas


def to_ascii(path) -> list[str]:
    img = Image.open(path).convert("L")
    img = img.resize((ASCII_COLS, ASCII_ROWS), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0

    # brilho -> indice na rampa (0 = claro/espaco, ultimo = escuro/denso)
    dark = np.power(1.0 - arr, GAMMA)
    idx = np.clip((dark * len(RAMP)).astype(int), 0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def build_svg(lines: list[str]) -> str:
    width = PAD * 2 + ASCII_COLS * CHAR_W
    height = PAD * 2 + ASCII_ROWS * LINE_H

    defs: list[str] = []
    texts: list[str] = []
    cursors: list[str] = []

    for row, line in enumerate(lines):
        if not line:
            continue
        begin = row * STAGGER
        span = len(line) * CHAR_W
        y_top = PAD + row * LINE_H
        baseline = y_top + LINE_H - 3.0
        clip_id = f"r{row}"

        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{PAD:.1f}" y="{y_top:.1f}" width="0" height="{LINE_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{span:.1f}" '
            f'begin="{begin:.2f}s" dur="{LINE_DUR:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        texts.append(
            f'<text x="{PAD:.1f}" y="{baseline:.1f}" clip-path="url(#{clip_id})" '
            f'textLength="{span:.1f}" lengthAdjust="spacing" '
            f'xml:space="preserve">{escape(line)}</text>'
        )
        cursors.append(
            f'<rect x="{PAD:.1f}" y="{y_top:.1f}" width="{CHAR_W:.1f}" '
            f'height="{LINE_H:.1f}" fill="{ACCENT}" opacity="0">'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{PAD:.1f}" to="{PAD + span:.1f}" '
            f'begin="{begin:.2f}s" dur="{LINE_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + LINE_DUR:.2f}s"/>'
            f"</rect>"
        )

    nl = "\n"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="Retrato em ASCII">
<rect width="100%" height="100%" fill="{BG}"/>
<defs>
{nl.join(defs)}
</defs>
<g font-family="{MONO}" font-size="{FONT_SIZE:.1f}" fill="{FG}">
{nl.join(texts)}
</g>
{nl.join(cursors)}
</svg>
"""


def main() -> None:
    if not PREPPED.exists():
        raise SystemExit("assets/source-prepped.png nao existe -- rode prep_photo.py antes")

    lines = to_ascii(PREPPED)
    # newline="\n" para o arquivo sair identico no Windows e no runner Linux
    OUT.write_text(build_svg(lines), encoding="utf-8", newline="\n")

    ink = sum(1 for line in lines for ch in line if ch != " ")
    total = len(lines) * ASCII_COLS
    print(f"  -> {OUT.name}  ({ASCII_COLS}x{ASCII_ROWS}, {100 * ink / total:.0f}% de tinta)")


if __name__ == "__main__":
    main()
