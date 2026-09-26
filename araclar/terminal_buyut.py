"""Terminal ekran görüntülerini videodaki panel boyutunda (740×462) yeniden çizer — yazı videoda 1:1, okunur.

Kaynak: terminal.py'nin yanına bıraktığı ham çıktı <ad>.txt (ilk satır "$ komut"). İçerik AYNI gerçek çıktıdır;
yalnız çizim boyutu değişir. Eski görüntü ekran_eski/<ders>/<ad>.png olarak saklanır.

    uv run python araclar/terminal_buyut.py            # hepsi
    uv run python araclar/terminal_buyut.py 2.2 3.1    # yalnız bu dersler
"""
from __future__ import annotations

import html
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from araclar.ekran import LAB  # noqa: E402

G, Y = 740, 462
FONT = LAB / "site" / "fonts"
SABLON = """<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><style>
@font-face {{ font-family: "T"; src: url("{f1}") format("woff2"); unicode-range: U+0000-00FF, U+2000-206F, U+20AC, U+2212; }}
@font-face {{ font-family: "T"; src: url("{f2}") format("woff2"); unicode-range: U+0100-024F, U+1E00-1EFF; }}
html, body {{ margin: 0; width: {g}px; height: {y}px; background: #0f141f; overflow: hidden; }}
pre {{ margin: 0; padding: 16px 20px; height: 100%; box-sizing: border-box; overflow: hidden; white-space: pre-wrap;
  word-break: break-word; font: {b}px/{lh} "T", monospace; font-variant-ligatures: none; color: #d6dbe6; }}
.k {{ color: #7ee2a8; }} .i {{ color: #7aa2f7; }} .n {{ color: #8b94a8; font-size: {nb}px; }}
</style></head><body><pre id="e">{not_}<span class="i">~/lab $</span> <span class="k">{komut}</span>
{cikti}<span class="i">~/lab $</span> ▍</pre></body></html>"""


def ciz(txt: Path) -> None:
    from playwright.sync_api import sync_playwright
    satir = txt.read_text(encoding="utf-8").rstrip("\n").split("\n")
    komut, cikti = satir[0][2:], satir[1:]
    png = txt.with_suffix(".png")
    eski = LAB / "ekran_eski" / txt.parent.name / png.name
    if not eski.exists():
        eski.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(png, eski)
    with sync_playwright() as p, tempfile.TemporaryDirectory() as gd:
        t = p.chromium.launch()
        s = t.new_page(viewport={"width": G, "height": Y})
        f = Path(gd) / "t.html"

        lh = 1.42

        def dene(b: int, gizli: int) -> bool:
            not_ = f'<span class="n">… ilk {gizli} satır sığmadı (tamamı {txt.name})</span>\n' if gizli else ""
            f.write_text(SABLON.format(f1=(FONT / "jetbrains-mono-400-latin.woff2").as_uri(),
                                       f2=(FONT / "jetbrains-mono-400-latin-ext.woff2").as_uri(), g=G, y=Y, b=b, lh=lh, nb=max(12, b - 4),
                                       komut=html.escape(komut), not_=not_,
                                       cikti="".join(html.escape(x) + "\n" for x in cikti[gizli:])), encoding="utf-8")
            s.goto(f.as_uri())
            s.evaluate("document.fonts.ready.then(() => true)")
            return s.evaluate("(() => { const e = document.getElementById('e'); return e.scrollHeight <= e.clientHeight; })()")

        b, gizli = 20, 0
        while not dene(b, gizli):
            if b > 14:
                b -= 1
            elif lh > 1.2:
                lh = 1.2
            elif gizli < len(cikti):
                gizli += 1
            else:
                break
        s.screenshot(path=str(png))
        t.close()
    print(f"{png.relative_to(LAB)} · {b}px{f' · ilk {gizli} satır gizli' if gizli else ''}")


def main() -> None:
    dersler = sys.argv[1:]
    for txt in sorted((LAB / "ekran").glob("*/*.txt")):
        if dersler and txt.parent.name not in dersler:
            continue
        if txt.name.endswith(".py.txt") or not txt.with_suffix(".png").exists():
            continue
        if not txt.read_text(encoding="utf-8").startswith("$ "):
            continue
        ciz(txt)


if __name__ == "__main__":
    main()
