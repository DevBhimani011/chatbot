# Backend Service

## Requirements

### Python Dependencies
Install the required python packages:
```bash
pip install -r requirements.txt
```

### OCR Setup (Tesseract)
This project uses `pytesseract` for OCR on scanned PDFs. You must install the Tesseract-OCR engine.

**Windows:**
1. Download the installer from [UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install Tesseract.
3. Add the Tesseract installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your system's PATH environment variable.
4. Verify by running `tesseract --version` in your terminal.

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**MacOS:**
```bash
brew install tesseract
```
