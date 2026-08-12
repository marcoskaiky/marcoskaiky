"""Ponto unico de edicao do perfil.

Todo texto que aparece nos SVGs vive aqui. Os scripts de render nao tem
conteudo hardcoded -- mude aqui e rode `python scripts/build_all.py`.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"

# --------------------------------------------------------------------------
# Identidade
# --------------------------------------------------------------------------
USERNAME = "marcoskaiky"
DISPLAY_NAME = "Marcos Kaiky"
PROMPT = "marcos@github"

# --------------------------------------------------------------------------
# Paleta (tons do GitHub dark)
# --------------------------------------------------------------------------
BG = "#0d1117"
FG = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#39d353"
ACCENT_2 = "#58a6ff"
BORDER = "#30363d"

# Verde do heatmap: 0 = sem contribuicao -> 5 = dia excepcional (neon)
HEAT_PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# --------------------------------------------------------------------------
# Conteudo do cartao neofetch
# --------------------------------------------------------------------------
# ("chave", "valor") -- chave vazia continua a linha anterior;
# ("---", "") desenha um separador.
INFO_ROWS = [
    ("OS", "Full Stack Developer & Data Analyst"),
    ("Host", "Umuarama, PR - Brazil"),
    ("Kernel", "Sistemas para Internet"),
    ("Shell", "building software & AI products"),
    ("---", ""),
    ("Focus", "Backend Architecture - Data Analytics"),
    ("", "Business Intelligence - AI Solutions"),
    ("Languages", "TypeScript - JavaScript - Java - Python - PHP"),
    ("Frameworks", "Node - Vue - React - React Native - Spring"),
    ("Cloud", "AWS - AWS Lambda - Docker"),
    ("AI", "LangChain - LLM apps"),
    ("---", ""),
    ("LinkedIn", "in/marcos-kaiky"),
    ("Email", "mkaikygarcia@gmail.com"),
]

# --------------------------------------------------------------------------
# Retrato ASCII
# --------------------------------------------------------------------------
ASCII_COLS = 100
ASCII_ROWS = 53
# claro (esparso) -> escuro (denso). O espaco inicial apaga o fundo.
RAMP = " .`:-=+*cs#%@"
