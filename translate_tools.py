from __future__ import annotations

import io
from typing import Literal

import fitz  # PyMuPDF
import pytesseract
from deep_translator import GoogleTranslator
from PIL import Image

from converter import _ensure_tesseract_cmd, _resolve_ocr_lang


def _chunk_text(text: str, max_len: int = 3500) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n"):
        part = paragraph.strip()
        if not part:
            part = "\n"
        if len(current) + len(part) + 1 <= max_len:
            current += ("\n" if current else "") + part
        else:
            if current:
                chunks.append(current)
            if len(part) <= max_len:
                current = part
            else:
                # Hard split very long text safely.
                for i in range(0, len(part), max_len):
                    chunks.append(part[i : i + max_len])
                current = ""
    if current:
        chunks.append(current)
    return chunks


def _extract_text_per_page(
    pdf_bytes: bytes,
    method: Literal["Direct Text", "OCR"],
    ocr_lang: str,
) -> list[str]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texts: list[str] = []
    if method == "OCR":
        _ensure_tesseract_cmd()
        ocr_lang = _resolve_ocr_lang(ocr_lang)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            texts.append(pytesseract.image_to_string(image, lang=ocr_lang).strip())
    else:
        for page in doc:
            texts.append(page.get_text("text").strip())
    return texts


def translate_pdf(
    pdf_bytes: bytes,
    source_lang: str,
    target_lang: str,
    method: Literal["Direct Text", "OCR"] = "Direct Text",
    ocr_lang: str = "eng",
) -> tuple[bytes, bytes]:
    page_texts = _extract_text_per_page(pdf_bytes, method=method, ocr_lang=ocr_lang)
    translator = GoogleTranslator(source=source_lang, target=target_lang)

    translated_pages: list[str] = []
    for text in page_texts:
        if not text:
            translated_pages.append("")
            continue
        translated_parts = [translator.translate(chunk) or "" for chunk in _chunk_text(text)]
        translated_pages.append("\n".join(part for part in translated_parts if part))

    out_doc = fitz.open()
    for i, translated in enumerate(translated_pages, start=1):
        page = out_doc.new_page(width=595, height=842)  # A4
        header = f"Translated Page {i}"
        page.insert_text((36, 40), header, fontsize=11, fontname="helv")
        content = translated if translated else "(No text detected)"
        page.insert_textbox(
            fitz.Rect(36, 58, 559, 806),
            content,
            fontsize=10.5,
            fontname="helv",
            align=0,
        )

    translated_pdf = out_doc.tobytes()
    merged_txt = "\n\n".join(
        f"=== Page {i} ===\n{txt}" for i, txt in enumerate(translated_pages, start=1)
    ).encode("utf-8")
    return translated_pdf, merged_txt
