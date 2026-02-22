# PDF @Sundara

Aplikasi ini adalah toolbox PDF seperti iLovePDF + PDF ke Excel.

## Fitur

- PDF ke Excel (1 sheet, dengan/ tanpa OCR)
- Merge PDF
- Split PDF (per halaman ke ZIP)
- Extract pages (contoh range `1-3,5`)
- Rotate PDF (90/180/270)
- Image to PDF
- Translate PDF (output `translated.pdf` + `translated.txt`)

## Jalankan Lokal (Windows)

1. Buka folder ini
2. Jalankan `start_portable.bat`
3. Buka `http://127.0.0.1:8502`

## Deploy Cloud (Railway)

1. Push repo ini ke GitHub.
2. Di Railway: New Project -> Deploy from GitHub Repo.
3. Railway akan pakai `Dockerfile` otomatis.
4. Tunggu build selesai, lalu buka URL publik Railway.

File deploy yang dipakai:
- `Dockerfile`
- `.dockerignore`
- `railway.json`

## Catatan OCR

- Mode OCR butuh Tesseract OCR.
- Di cloud, Tesseract sudah ikut di Docker image.
- Jika bahasa `ind` tidak tersedia, aplikasi fallback ke bahasa yang tersedia (misalnya `eng`).
