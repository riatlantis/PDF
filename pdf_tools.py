from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter


def merge_pdfs(pdf_files: list[tuple[str, bytes]]) -> bytes:
    writer = PdfWriter()
    for _, pdf_bytes in pdf_files:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def rotate_pdf(pdf_bytes: bytes, degrees: int) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _parse_page_spec(page_spec: str, total_pages: int) -> list[int]:
    page_spec = (page_spec or "").strip()
    if not page_spec:
        raise ValueError("Range halaman kosong.")

    pages: set[int] = set()
    parts = [p.strip() for p in page_spec.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a_str, b_str = [x.strip() for x in part.split("-", 1)]
            a, b = int(a_str), int(b_str)
            if a > b:
                a, b = b, a
            for p in range(a, b + 1):
                if 1 <= p <= total_pages:
                    pages.add(p)
        else:
            p = int(part)
            if 1 <= p <= total_pages:
                pages.add(p)

    ordered = sorted(pages)
    if not ordered:
        raise ValueError("Tidak ada halaman valid sesuai range.")
    return ordered


def extract_pages(pdf_bytes: bytes, page_spec: str) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    selected = _parse_page_spec(page_spec, len(reader.pages))
    writer = PdfWriter()
    for page_number in selected:
        writer.add_page(reader.pages[page_number - 1])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def split_pdf_to_zip(pdf_bytes: bytes, base_name: str) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    mem_zip = io.BytesIO()
    safe_base = Path(base_name).stem or "document"
    with zipfile.ZipFile(mem_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            page_bytes = io.BytesIO()
            writer.write(page_bytes)
            zipf.writestr(f"{safe_base}_page_{i}.pdf", page_bytes.getvalue())
    return mem_zip.getvalue()


def images_to_pdf(image_files: list[tuple[str, bytes]]) -> bytes:
    if not image_files:
        raise ValueError("Tidak ada gambar diupload.")

    pil_images: list[Image.Image] = []
    for _, img_bytes in image_files:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        pil_images.append(img)

    out = io.BytesIO()
    first, rest = pil_images[0], pil_images[1:]
    first.save(out, format="PDF", save_all=True, append_images=rest)
    return out.getvalue()
