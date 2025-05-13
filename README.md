# Mac용 PDF OCR 변환 스크립트 (Apple Vision API 기반)

이 스크립트는 **PDF 파일을 이미지로 변환**하고, 각 페이지를 **macOS의 Apple Vision Framework를 이용해 OCR 처리**하여 **모든 텍스트를 하나의 `output.txt` 파일로 저장**합니다.

---

## 기능

- PDF 파일 입력
- 각 페이지를 고해상도 이미지로 저장
- macOS Vision API(`VNRecognizeTextRequest`)를 이용한 텍스트 인식
- `output.txt`로 페이지별 OCR 결과 저장

---

## 설치

Python 3.x 환경에서 아래 패키지를 설치하세요:

```bash
pip install pymupdf pillow pyobjc-core pyobjc-framework-Vision pyobjc-framework-Quartz
```

## 실행
python ocr.py
