"""
OCR-based name extraction from Google Maps screenshots.
Uses PaddleOCR if available, falls back to basic pixel analysis.
"""
import subprocess
import sys


def check_ocr_available():
    """Check if any OCR engine is installed."""
    checks = [
        ("paddleocr", lambda: __import__("paddleocr")),
        ("tesseract", lambda: subprocess.run(["tesseract", "--version"], capture_output=True)),
    ]
    for name, check_fn in checks:
        try:
            check_fn()
            return name
        except Exception:
            continue
    return None


def extract_text_paddle(image_path):
    """Extract text from an image using PaddleOCR."""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        result = ocr.ocr(str(image_path), cls=False)
        texts = []
        for line_group in result:
            if line_group is None:
                continue
            for item in line_group:
                bbox, (text, confidence) = item
                if confidence and confidence > 0.5 and text and len(text.strip()) > 2:
                    texts.append((text.strip(), confidence, bbox))
        return texts
    except Exception as e:
        return []


def extract_text_tesseract(image_path):
    """Extract text from an image using Tesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        texts = []
        for i, text in enumerate(data["text"]):
            text = text.strip()
            conf = int(data["conf"][i]) if data["conf"][i] != -1 else 0
            if text and len(text) > 2 and conf > 30:
                x = data["left"][i]
                y = data["top"][i]
                texts.append((text, conf / 100.0, (x, y, x + data["width"][i], y + data["height"][i])))
        return texts
    except Exception as e:
        return []


def extract_text(image_path, engine="auto"):
    """Extract text from an image using the best available OCR engine."""
    if engine == "auto":
        available = check_ocr_available()
        if available == "paddleocr":
            return extract_text_paddle(image_path)
        elif available == "tesseract":
            return extract_text_tesseract(image_path)
        else:
            return []
    elif engine == "paddleocr":
        return extract_text_paddle(image_path)
    elif engine == "tesseract":
        return extract_text_tesseract(image_path)
    return []
