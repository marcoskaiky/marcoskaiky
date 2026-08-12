"""Prepara uma foto para virar arte ASCII.

Um rosto com iluminacao uniforme -- ou uma selfie com parede de fundo -- vira
uma mancha escura ilegivel. A ordem dos passos importa:

  1. recorta o fundo (rembg) para isolar o sujeito e guarda a mascara alpha;
  2. enquadra no sujeito, para o retrato preencher a grade;
  3. aplica CLAHE -- equalizacao de histograma adaptativa com limite de
     contraste -- que e o que da realce e sombra reais a um rosto plano;
  4. reimpoe a mascara: tudo fora do sujeito volta a branco PURO.

O passo 4 nao e opcional. CLAHE amplifica contraste local, entao uma area lisa
(a parede atras) sai como cinza ruidoso -- e cinza vira tinta na rampa ASCII.
Reimpor a mascara depois garante que o fundo caia no glifo espaco.

Uso:
    python scripts/prep_photo.py                  # baixa o avatar do GitHub
    python scripts/prep_photo.py foto.jpg         # usa um arquivo local

Saida: assets/source-prepped.png
"""

from __future__ import annotations

import math
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageOps

from config import ASSETS, USERNAME

AVATAR_URL = f"https://github.com/{USERNAME}.png?size=1024"
SOURCE = ASSETS / "source.png"
PREPPED = ASSETS / "source-prepped.png"

ALPHA_MIN = 24      # abaixo disso e fundo
MARGIN = 0.04       # folga ao redor do sujeito


def download_avatar() -> "Image.Image":
    print(f"  baixando {AVATAR_URL}")
    req = urllib.request.Request(AVATAR_URL, headers={"User-Agent": "profile-art"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        SOURCE.write_bytes(resp.read())
    print(f"  -> {SOURCE.relative_to(ASSETS.parent)}")
    return Image.open(SOURCE)


def cut_background(img: "Image.Image") -> "Image.Image":
    """Isola o sujeito com rembg. Sem rembg, devolve tudo opaco."""
    try:
        from rembg import remove
    except ImportError:
        print("  rembg ausente -- fundo mantido (retrato tende a saturar de tinta)")
        return img.convert("RGBA")
    print("  rembg: recortando fundo")
    return remove(img.convert("RGBA"))


def crop_to_subject(rgba: "Image.Image") -> "Image.Image":
    """Enquadra no sujeito e completa para quadrado, com fundo transparente."""
    alpha = np.asarray(rgba.getchannel("A"))
    ys, xs = np.nonzero(alpha >= ALPHA_MIN)
    if ys.size == 0:
        return rgba

    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    pad = int(max(bottom - top, right - left) * MARGIN)
    box = (
        max(0, left - pad), max(0, top - pad),
        min(rgba.width, right + 1 + pad), min(rgba.height, bottom + 1 + pad),
    )
    cropped = rgba.crop(box)

    side = max(cropped.width, cropped.height)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
    print(f"  enquadrado: {rgba.width}x{rgba.height} -> {side}x{side}")
    return canvas


def flatten_on_white(rgba: "Image.Image") -> "Image.Image":
    canvas = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    canvas.alpha_composite(rgba)
    return canvas.convert("L")


def clahe_numpy(gray: np.ndarray, grid: int = 8, clip_limit: float = 2.5) -> np.ndarray:
    """CLAHE em numpy puro.

    Divide a imagem em `grid`x`grid` blocos, monta uma LUT por bloco (com o
    histograma clipado e o excedente redistribuido) e interpola bilinearmente
    entre as LUTs vizinhas, para nao aparecer costura entre os blocos.
    """
    h, w = gray.shape
    th, tw = math.ceil(h / grid), math.ceil(w / grid)
    padded = np.pad(gray, ((0, th * grid - h), (0, tw * grid - w)), mode="reflect")

    luts = np.empty((grid, grid, 256), dtype=np.float32)
    limit = max(1.0, clip_limit * (th * tw) / 256.0)
    for gy in range(grid):
        for gx in range(grid):
            tile = padded[gy * th:(gy + 1) * th, gx * tw:(gx + 1) * tw]
            hist = np.bincount(tile.ravel(), minlength=256).astype(np.float32)
            excess = np.maximum(hist - limit, 0.0).sum()
            hist = np.minimum(hist, limit) + excess / 256.0
            cdf = np.cumsum(hist)
            luts[gy, gx] = 255.0 * cdf / cdf[-1]

    fy = np.clip((np.arange(h) + 0.5) / th - 0.5, 0, grid - 1)
    fx = np.clip((np.arange(w) + 0.5) / tw - 0.5, 0, grid - 1)
    y0 = np.floor(fy).astype(np.int32)
    x0 = np.floor(fx).astype(np.int32)
    y1 = np.minimum(y0 + 1, grid - 1)
    x1 = np.minimum(x0 + 1, grid - 1)
    wy = (fy - y0).astype(np.float32)[:, None]
    wx = (fx - x0).astype(np.float32)[None, :]

    def mapped(gy: np.ndarray, gx: np.ndarray) -> np.ndarray:
        return luts[gy[:, None], gx[None, :], gray]

    out = (
        mapped(y0, x0) * (1 - wy) * (1 - wx)
        + mapped(y0, x1) * (1 - wy) * wx
        + mapped(y1, x0) * wy * (1 - wx)
        + mapped(y1, x1) * wy * wx
    )
    return np.clip(out, 0, 255).astype(np.uint8)


def local_contrast(gray: "Image.Image") -> "Image.Image":
    arr = np.asarray(gray, dtype=np.uint8)
    try:
        import cv2
    except ImportError:
        print("  CLAHE: numpy (opencv ausente)")
        return Image.fromarray(clahe_numpy(arr))
    print("  CLAHE: opencv")
    op = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return Image.fromarray(op.apply(arr))


def restore_background(gray: "Image.Image", rgba: "Image.Image") -> "Image.Image":
    """Devolve o fundo a branco puro e suaviza a borda do recorte."""
    alpha = np.asarray(rgba.getchannel("A")).astype(np.float32) / 255.0
    arr = np.asarray(gray).astype(np.float32)
    blended = arr * alpha + 255.0 * (1.0 - alpha)
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        img = Image.open(sys.argv[1])
        print(f"  fonte: {sys.argv[1]}")
    elif SOURCE.exists():
        img = Image.open(SOURCE)
        print(f"  fonte: {SOURCE.name} (cache)")
    else:
        img = download_avatar()

    rgba = crop_to_subject(cut_background(ImageOps.exif_transpose(img)))

    gray = flatten_on_white(rgba)
    gray = local_contrast(gray)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = restore_background(gray, rgba)

    gray.save(PREPPED)
    print(f"  -> {PREPPED.relative_to(ASSETS.parent)}  ({gray.width}x{gray.height})")


if __name__ == "__main__":
    main()
