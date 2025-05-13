import os
from pathlib import Path
import fitz  # PyMuPDF
from Cocoa import NSURL
from Quartz import CGImageSourceCreateWithURL, CGImageSourceCreateImageAtIndex
import Quartz
import Vision
from PIL import Image

# ===== OCR 처리 함수 =====
def handle_results(results):
    texts = []
    for observation in results:
        top_candidate = observation.topCandidates_(1).firstObject()
        if top_candidate:
            texts.append(top_candidate.string())
    return "\n".join(texts)

def ocr_image_with_vision(image_path: Path) -> str:
    nsurl = NSURL.fileURLWithPath_(str(image_path))
    src = CGImageSourceCreateWithURL(nsurl, None)
    cg_image = CGImageSourceCreateImageAtIndex(src, 0, None)
    
    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(None)
    request.setRecognitionLanguages_(["ko-KR", "en-US"])
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, {})
    success = handler.performRequests_error_([request], None)
    
    if success:
        return handle_results(request.results())
    else:
        return f"[ERROR] OCR 실패: {image_path}"

# ===== PDF to Image + OCR =====
def pdf_to_text(pdf_path: str, output_txt: str = "output.txt"):
    pdf_path = Path(pdf_path)
    output_txt = Path(output_txt)
    temp_dir = Path("./__pdf_images__")
    temp_dir.mkdir(exist_ok=True)

    doc = fitz.open(str(pdf_path))
    all_texts = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img_path = temp_dir / f"page_{page_num+1:03}.png"
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(img_path)

        print(f"[+] OCR 중: {img_path}")
        text = ocr_image_with_vision(img_path)
        all_texts.append(f"\n--- Page {page_num + 1} ---\n{text}")

    # 결과 저장
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_texts))

    print(f"\n✅ 완료! 전체 OCR 결과가 {output_txt}에 저장되었습니다.")

# ===== 실행 예시 =====
if __name__ == "__main__":
    # PDF 파일 경로 지정
    pdf_file = "sample.pdf"  # <- 여기에 OCR하고자 하는 PDF 파일 이름 입력
    pdf_to_text(pdf_file)
