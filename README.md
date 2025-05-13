# Mac용 PDF OCR 변환 스크립트 (Apple Vision API 기반)

이 스크립트는 **PDF 파일을 이미지로 변환**하고, 각 페이지를 **macOS의 Apple Vision Framework를 이용해 OCR 처리**하여 **모든 텍스트를 하나의 `output.txt` 파일로 저장**합니다.

## 기능

- PDF 파일 입력
- 각 페이지를 고해상도 이미지로 저장
- macOS Vision API(`VNRecognizeTextRequest`)를 이용한 텍스트 인식
- `output.txt`로 페이지별 OCR 결과 저장

## 설치

Python 3.x 환경에서 아래 패키지를 설치하세요:
```bash
pip install pymupdf pillow pyobjc-core pyobjc-framework-Vision pyobjc-framework-Quartz
```

## 실행
python ocr.py

## 결과물
- __pdf_images__/page_001.png 등: 임시로 생성된 이미지 파일
- output.txt: 전체 페이지의 텍스트가 저장된 파일

## 커스터마이징
- OCR 언어 설정 변경: "ko-KR", "en-US" (한국어 + 영어)
- 해상도 변경: pix = page.get_pixmap(dpi=300)
- OCR 결과를 파일별 또는 JSON 등으로 분할 저장 가능

## 주의사항
- PDF 내 텍스트가 이미지가 아닌 벡터 기반이라면, PyMuPDF 대신 Tesseract 또는 직접 파싱을 권장합니다.
- pyobjc-framework-Vision은 Apple 공식 API의 Python 바인딩이지만, 일부 제한이 있습니다.
- 너무 낮은 해상도의 이미지에서는 OCR 인식률이 떨어질 수 있습니다.

## 라이선스
MIT License

## 기여
이 스크립트는 개인용 OCR 자동화 목적을 위해 설계되었습니다. 개선 제안이나 피드백은 언제든지 환영합니다!
