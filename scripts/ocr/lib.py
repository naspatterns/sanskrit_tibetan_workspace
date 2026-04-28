"""OCR helpers — wrap pdftoppm + tesseract for cached, parallel page OCR.

Each PDF gets a per-page text + word-level confidence cache under
data/ocr_cache/<slug>/p{NNNNN}.{txt,conf}. Re-runs read from cache.

Uses subprocess directly (not pdf2image/pytesseract) for speed —
pytesseract spawns one tesseract per call; we already do that. pdf2image
adds Pillow loading we don't need.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = ROOT / "data" / "ocr_cache"


@dataclass
class PageOCR:
    page: int
    text: str
    conf: float  # 0-100, mean of word-level conf (positive only)
    n_words: int


def page_count(pdf_path: Path) -> int:
    """Use pdfinfo to get page count."""
    out = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"pdfinfo did not report Pages for {pdf_path}")


def _ocr_image(image_path: Path, langs: str, psm: int) -> tuple[str, list[float]]:
    """Run tesseract on a single image; return (text, list of word confs)."""
    td_path = image_path.parent
    text_out = td_path / f"{image_path.stem}_text"
    subprocess.run(
        [
            "tesseract", str(image_path), str(text_out),
            "-l", langs,
            "--psm", str(psm),
            "-c", "preserve_interword_spaces=1",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    text = (text_out.with_suffix(".txt")).read_text(encoding="utf-8")

    tsv_out = td_path / f"{image_path.stem}_tsv"
    subprocess.run(
        [
            "tesseract", str(image_path), str(tsv_out),
            "-l", langs,
            "--psm", str(psm),
            "-c", "preserve_interword_spaces=1",
            "tsv",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tsv = (tsv_out.with_suffix(".tsv")).read_text(encoding="utf-8")
    confs: list[float] = []
    for line in tsv.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) < 12:
            continue
        try:
            c = float(cols[10])
        except ValueError:
            continue
        if c < 0:
            continue
        if not cols[11].strip():
            continue
        confs.append(c)
    return text, confs


def _split_image_columns(png: Path, n_cols: int, overlap_px: int = 30) -> list[Path]:
    """Split image horizontally into n_cols evenly-sized parts (with overlap).

    Returns paths to the cropped column images.
    """
    if n_cols <= 1:
        return [png]
    from PIL import Image  # lazy import — only needed for multi-col docs

    im = Image.open(png)
    w, h = im.size
    col_w = w // n_cols
    out = []
    for i in range(n_cols):
        x0 = max(0, i * col_w - overlap_px)
        x1 = min(w, (i + 1) * col_w + overlap_px) if i < n_cols - 1 else w
        crop = im.crop((x0, 0, x1, h))
        out_path = png.parent / f"{png.stem}_col{i}.png"
        crop.save(out_path)
        out.append(out_path)
    return out


def _ocr_page_uncached(
    pdf_path: Path,
    page: int,
    langs: str,
    psm: int,
    dpi: int,
    columns: int = 1,
) -> PageOCR:
    """Render one page to PNG (temp), run tesseract, return text + conf.

    If columns > 1, split image horizontally and OCR each column separately,
    concatenating results in left-to-right order.
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        png_prefix = td_path / "page"
        subprocess.run(
            [
                "pdftoppm",
                "-r", str(dpi),
                "-f", str(page),
                "-l", str(page),
                "-png",
                str(pdf_path),
                str(png_prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pngs = sorted(td_path.glob("page-*.png"))
        if not pngs:
            return PageOCR(page=page, text="", conf=0.0, n_words=0)
        png = pngs[0]

        col_imgs = _split_image_columns(png, columns)
        all_text_parts: list[str] = []
        all_confs: list[float] = []
        for ci, col_img in enumerate(col_imgs):
            text, confs = _ocr_image(col_img, langs, psm)
            if columns > 1 and ci > 0:
                all_text_parts.append(f"\n--- COL {ci} ---\n")
            all_text_parts.append(text)
            all_confs.extend(confs)
        text = "".join(all_text_parts)
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0.0
        return PageOCR(page=page, text=text, conf=avg_conf, n_words=len(all_confs))


def ocr_page_cached(
    slug: str,
    pdf_path: Path,
    page: int,
    langs: str,
    psm: int = 4,
    dpi: int = 300,
    columns: int = 1,
) -> PageOCR:
    """OCR a single page with disk cache.

    Cache key includes psm/dpi/columns/langs so changing settings invalidates.
    """
    cache_dir = CACHE_ROOT / slug
    cache_dir.mkdir(parents=True, exist_ok=True)
    txt_file = cache_dir / f"p{page:05d}.txt"
    conf_file = cache_dir / f"p{page:05d}.json"
    if txt_file.exists() and conf_file.exists():
        try:
            meta = json.loads(conf_file.read_text())
            settings_match = (
                meta.get("langs") == langs
                and meta.get("psm") == psm
                and meta.get("dpi") == dpi
                and meta.get("columns", 1) == columns
            )
            if settings_match:
                return PageOCR(
                    page=page,
                    text=txt_file.read_text(encoding="utf-8"),
                    conf=meta["conf"],
                    n_words=meta["n_words"],
                )
        except (json.JSONDecodeError, KeyError):
            pass

    result = _ocr_page_uncached(pdf_path, page, langs, psm, dpi, columns)
    txt_file.write_text(result.text, encoding="utf-8")
    conf_file.write_text(json.dumps({
        "conf": result.conf,
        "n_words": result.n_words,
        "langs": langs,
        "psm": psm,
        "dpi": dpi,
        "columns": columns,
    }))
    return result


def _worker(args: tuple) -> PageOCR:
    slug, pdf_path, page, langs, psm, dpi, columns = args
    return ocr_page_cached(slug, pdf_path, page, langs, psm, dpi, columns)


def ocr_pdf_parallel(
    slug: str,
    pdf_path: Path,
    pages: list[int],
    langs: str,
    psm: int = 4,
    dpi: int = 300,
    workers: int = 6,
    progress_every: int = 25,
    columns: int = 1,
) -> list[PageOCR]:
    """OCR a set of pages in parallel using process pool. Yields cached results.

    Returns list ordered by page number.
    """
    args_list = [(slug, pdf_path, p, langs, psm, dpi, columns) for p in pages]
    results: dict[int, PageOCR] = {}
    completed = 0
    total = len(pages)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_worker, a): a[2] for a in args_list}
        for fut in as_completed(futures):
            page = futures[fut]
            try:
                r = fut.result()
                results[page] = r
            except Exception as exc:
                print(f"  page {page} failed: {exc}", flush=True)
                results[page] = PageOCR(page=page, text="", conf=0.0, n_words=0)
            completed += 1
            if completed % progress_every == 0 or completed == total:
                with_words = [r for r in results.values() if r.n_words > 0]
                avg_conf = (
                    sum(r.conf for r in with_words) / len(with_words)
                    if with_words
                    else 0.0
                )
                print(
                    f"  OCR {completed}/{total} pages (avg conf so far: {avg_conf:.1f})",
                    flush=True,
                )

    return [results[p] for p in sorted(results)]


def assert_tools_available() -> None:
    """Sanity check pdftoppm + tesseract are installed."""
    for tool in ("pdftoppm", "tesseract", "pdfinfo"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} not on PATH — install poppler/tesseract")


def load_cached_pages(slug: str, max_page: int | None = None) -> list[PageOCR]:
    """Read all cached pages for a slug, in page-number order.

    Useful for re-parsing without re-OCRing (e.g. parser tweak; or extracting
    partial results from an interrupted OCR run).
    """
    cache_dir = CACHE_ROOT / slug
    if not cache_dir.exists():
        return []
    out: list[PageOCR] = []
    for txt_file in sorted(cache_dir.glob("p*.txt")):
        page = int(txt_file.stem.lstrip("p"))
        if max_page is not None and page > max_page:
            continue
        conf_file = txt_file.with_suffix(".json")
        if not conf_file.exists():
            continue
        try:
            meta = json.loads(conf_file.read_text())
            text = txt_file.read_text(encoding="utf-8")
            out.append(
                PageOCR(
                    page=page,
                    text=text,
                    conf=meta.get("conf", 0.0),
                    n_words=meta.get("n_words", 0),
                )
            )
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return out
