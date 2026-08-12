"""Regenera os tres SVGs na ordem certa.

    python scripts/build_all.py           # tudo
    python scripts/build_all.py --heatmap # so o que muda todo dia
"""

from __future__ import annotations

import sys

import fetch_contributions
import render_heatmap_svg


def main() -> None:
    only_heatmap = "--heatmap" in sys.argv

    if not only_heatmap:
        import make_info_card
        import make_ascii_svg
        import prep_photo

        print("[1/4] preparando foto")
        prep_photo.main()
        print("[2/4] retrato ascii")
        make_ascii_svg.main()
        print("[3/4] cartao neofetch")
        make_info_card.main()

    print("[4/4] contribuicoes" if not only_heatmap else "[1/2] contribuicoes")
    fetch_contributions.main()
    print("      heatmap")
    render_heatmap_svg.main()
    print("pronto.")


if __name__ == "__main__":
    main()
