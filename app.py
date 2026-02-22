from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from converter import pdf_to_excel_preserve_layout
from pdf_tools import extract_pages, images_to_pdf, merge_pdfs, rotate_pdf, split_pdf_to_zip
from translate_tools import translate_pdf


st.set_page_config(page_title="PDF @Sundara", page_icon="PDF", layout="wide")

st.markdown(
    """
<style>
:root {
  --bg-1: #0b1220;
  --bg-2: #111b31;
  --card: rgba(255,255,255,.06);
  --line: rgba(255,255,255,.14);
  --text: #f2f5fb;
  --muted: #b7c2d9;
  --accent: #13b39a;
  --accent-2: #1a8fff;
}
.stApp {
  background: radial-gradient(1200px 500px at 10% -20%, #1e3258 0%, transparent 55%),
              radial-gradient(1200px 500px at 90% -20%, #153f4b 0%, transparent 55%),
              linear-gradient(180deg, var(--bg-2), var(--bg-1));
}
.block-container {
  max-width: 1150px;
  padding-top: 1.6rem;
  padding-bottom: 2.5rem;
}
.hero {
  background: linear-gradient(135deg, rgba(26,143,255,.2), rgba(19,179,154,.2));
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.1rem 1.3rem;
  margin-bottom: 1rem;
}
.hero h1 {
  margin: 0;
  color: var(--text);
  font-size: 1.85rem;
}
.hero p {
  margin: .35rem 0 0;
  color: var(--muted);
}
.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 1rem;
}
.panel-title {
  color: var(--text);
  font-weight: 600;
  margin-bottom: .45rem;
}
.small-note {
  color: var(--muted);
  font-size: .88rem;
}
div.stButton > button {
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  font-weight: 700;
}
div.stDownloadButton > button {
  border-radius: 11px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.08);
  color: #f7faff;
}
</style>
<div class="hero">
  <h1>PDF @Sundara</h1>
  <p>Suite alat PDF seperti iLovePDF: Merge, Split, Rotate, Extract, Image to PDF, dan PDF ke Excel + OCR.</p>
</div>
""",
    unsafe_allow_html=True,
)


# Keep conversion helper inside the app module for clarity of flow.
def _convert_pdf_to_excel(pdf_bytes: bytes, base_name: str, dpi: int, mode: str, ocr_lang: str) -> list[tuple[str, bytes]]:
    def _convert_and_read(with_ocr: bool) -> tuple[str, bytes]:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
            temp_output = Path(temp_file.name)

        try:
            pdf_to_excel_preserve_layout(
                pdf_bytes,
                temp_output,
                dpi=dpi,
                with_ocr=with_ocr,
                ocr_lang=ocr_lang.strip() or "eng",
            )
            output_name = f"{base_name}_{'with_ocr' if with_ocr else 'no_ocr'}.xlsx"
            return output_name, temp_output.read_bytes()
        finally:
            temp_output.unlink(missing_ok=True)

    if mode == "Tanpa OCR":
        return [_convert_and_read(with_ocr=False)]
    if mode == "Dengan OCR":
        return [_convert_and_read(with_ocr=True)]
    return [_convert_and_read(with_ocr=False), _convert_and_read(with_ocr=True)]


tab_excel, tab_merge, tab_split, tab_extract, tab_rotate, tab_img, tab_translate = st.tabs(
    [
        "PDF ke Excel",
        "Merge PDF",
        "Split PDF",
        "Extract Pages",
        "Rotate PDF",
        "Image to PDF",
        "Translate PDF",
    ]
)

with tab_excel:
    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Input PDF</div>', unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="excel_pdf")
        if uploaded_pdf is not None:
            st.markdown(f'<div class="small-note">File aktif: <b>{uploaded_pdf.name}</b></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Pengaturan</div>', unsafe_allow_html=True)
        dpi = st.slider("Kualitas (DPI)", min_value=120, max_value=300, value=200, step=10, key="excel_dpi")
        mode = st.radio(
            "Mode",
            options=["Tanpa OCR", "Dengan OCR", "Keduanya (2 file terpisah)"],
            index=0,
            key="excel_mode",
        )
        ocr_lang = st.text_input("Bahasa OCR", value="eng", help="Contoh: eng atau ind+eng", key="excel_ocr")
        st.markdown('<div class="small-note">Output: 1 sheet layout, OCR ditaruh di bawah tiap halaman.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Konversi PDF ke Excel", type="primary", disabled=uploaded_pdf is None, use_container_width=True, key="excel_btn"):
        try:
            with st.spinner("Memproses PDF ke Excel..."):
                files = _convert_pdf_to_excel(
                    pdf_bytes=uploaded_pdf.read(),
                    base_name=Path(uploaded_pdf.name).stem,
                    dpi=dpi,
                    mode=mode,
                    ocr_lang=ocr_lang,
                )
            st.success("Selesai.")
            for file_name, data in files:
                st.download_button(
                    f"Download {file_name}",
                    data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"dl_excel_{file_name}",
                )
        except Exception as exc:
            st.error(f"Gagal konversi: {exc}")

with tab_merge:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Gabungkan Banyak PDF Jadi Satu</div>', unsafe_allow_html=True)
    merge_files = st.file_uploader("Upload 2+ PDF", type=["pdf"], accept_multiple_files=True, key="merge_files")
    if st.button("Merge PDF", type="primary", disabled=not merge_files, use_container_width=True, key="merge_btn"):
        try:
            ordered_files = [(f.name, f.read()) for f in merge_files]
            merged = merge_pdfs(ordered_files)
            st.success("Merge selesai.")
            st.download_button(
                "Download merged.pdf",
                merged,
                file_name="merged.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="merge_dl",
            )
        except Exception as exc:
            st.error(f"Gagal merge: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_split:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Split PDF per Halaman</div>', unsafe_allow_html=True)
    split_file = st.file_uploader("Upload PDF", type=["pdf"], key="split_file")
    if st.button("Split Jadi ZIP", type="primary", disabled=split_file is None, use_container_width=True, key="split_btn"):
        try:
            zip_bytes = split_pdf_to_zip(split_file.read(), Path(split_file.name).stem)
            st.success("Split selesai.")
            st.download_button(
                "Download split_pages.zip",
                zip_bytes,
                file_name=f"{Path(split_file.name).stem}_split.zip",
                mime="application/zip",
                use_container_width=True,
                key="split_dl",
            )
        except Exception as exc:
            st.error(f"Gagal split: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_extract:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Ambil Halaman Tertentu</div>', unsafe_allow_html=True)
    extract_file = st.file_uploader("Upload PDF", type=["pdf"], key="extract_file")
    page_spec = st.text_input("Range halaman", value="1-3,5", help="Contoh: 1-3,5,8-10", key="extract_spec")
    if st.button("Extract Pages", type="primary", disabled=extract_file is None, use_container_width=True, key="extract_btn"):
        try:
            out = extract_pages(extract_file.read(), page_spec)
            st.success("Extract selesai.")
            st.download_button(
                "Download extracted.pdf",
                out,
                file_name=f"{Path(extract_file.name).stem}_extracted.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="extract_dl",
            )
        except Exception as exc:
            st.error(f"Gagal extract: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_rotate:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Putar Semua Halaman PDF</div>', unsafe_allow_html=True)
    rotate_file = st.file_uploader("Upload PDF", type=["pdf"], key="rotate_file")
    degrees = st.selectbox("Derajat", options=[90, 180, 270], index=0, key="rotate_deg")
    if st.button("Rotate PDF", type="primary", disabled=rotate_file is None, use_container_width=True, key="rotate_btn"):
        try:
            out = rotate_pdf(rotate_file.read(), int(degrees))
            st.success("Rotate selesai.")
            st.download_button(
                "Download rotated.pdf",
                out,
                file_name=f"{Path(rotate_file.name).stem}_rotated.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="rotate_dl",
            )
        except Exception as exc:
            st.error(f"Gagal rotate: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_img:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Gabungkan Gambar Menjadi PDF</div>', unsafe_allow_html=True)
    img_files = st.file_uploader(
        "Upload gambar",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff"],
        accept_multiple_files=True,
        key="img_files",
    )
    if st.button("Convert Image to PDF", type="primary", disabled=not img_files, use_container_width=True, key="img_btn"):
        try:
            out = images_to_pdf([(f.name, f.read()) for f in img_files])
            st.success("Konversi selesai.")
            st.download_button(
                "Download images.pdf",
                out,
                file_name="images.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="img_dl",
            )
        except Exception as exc:
            st.error(f"Gagal convert: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_translate:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Translate Isi PDF</div>', unsafe_allow_html=True)
    tr_file = st.file_uploader("Upload PDF", type=["pdf"], key="tr_file")
    c1, c2 = st.columns(2)
    with c1:
        src_lang = st.text_input("Bahasa sumber", value="auto", help="Contoh: auto, id, en", key="tr_src")
        extract_method = st.radio(
            "Metode baca teks",
            options=["Direct Text", "OCR"],
            index=0,
            key="tr_method",
        )
    with c2:
        tgt_lang = st.text_input("Bahasa tujuan", value="id", help="Contoh: id, en, ms", key="tr_tgt")
        ocr_lang = st.text_input("OCR lang", value="eng", help="Dipakai jika metode OCR", key="tr_ocr")

    if st.button("Translate PDF", type="primary", disabled=tr_file is None, use_container_width=True, key="tr_btn"):
        try:
            with st.spinner("Menerjemahkan PDF..."):
                out_pdf, out_txt = translate_pdf(
                    tr_file.read(),
                    source_lang=src_lang.strip() or "auto",
                    target_lang=tgt_lang.strip() or "id",
                    method=extract_method,
                    ocr_lang=ocr_lang.strip() or "eng",
                )
            stem = Path(tr_file.name).stem
            st.success("Terjemahan selesai.")
            st.download_button(
                "Download translated.pdf",
                out_pdf,
                file_name=f"{stem}_translated.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="tr_dl_pdf",
            )
            st.download_button(
                "Download translated.txt",
                out_txt,
                file_name=f"{stem}_translated.txt",
                mime="text/plain",
                use_container_width=True,
                key="tr_dl_txt",
            )
        except Exception as exc:
            st.error(f"Gagal translate: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

