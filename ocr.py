import os
import threading
from pathlib import Path
import fitz  # PyMuPDF
from Cocoa import NSURL
from Quartz import CGImageSourceCreateWithURL, CGImageSourceCreateImageAtIndex
import Quartz
import Vision
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import contextlib
import sys

stop_event = threading.Event()

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

def pdf_to_text_with_progress(pdf_path: str, output_txt: str, progress_var, progress_bar, status_label):
    pdf_path = Path(pdf_path)
    output_txt = Path(output_txt)
    temp_dir = Path("./__pdf_images__")
    temp_dir.mkdir(exist_ok=True)

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    all_texts = []

    for page_num in range(total_pages):
        if stop_event.is_set():
            status_label.config(text="⛔ 중단됨")
            return

        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img_path = temp_dir / f"page_{page_num+1:03}.png"
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(img_path)

        status_label.config(text=f"OCR 중: Page {page_num + 1}/{total_pages}")
        progress_var.set((page_num + 1) / total_pages * 100)
        progress_bar.update()

        text = ocr_image_with_vision(img_path)
        all_texts.append(f"\n--- Page {page_num + 1} ---\n{text}")

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_texts))

    status_label.config(text=f"✅ 완료: {output_txt}")
    progress_var.set(100)
    messagebox.showinfo("OCR 완료", f"OCR 결과가 다음에 저장되었습니다:\n{output_txt}")

    # 결과 파일 자동 열기 (macOS에서 TextEdit 등으로 열림)
    os.system(f"open {output_txt}")

def run_gui():
    def start_ocr():
        file_path = filedialog.askopenfilename(
            title="PDF 파일을 선택하세요",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return

        stop_event.clear()
        output_txt = "output.txt"

        thread = threading.Thread(
            target=pdf_to_text_with_progress,
            args=(file_path, output_txt, progress_var, progress_bar, status_label),
            daemon=True
        )
        thread.start()

    def stop_ocr():
        stop_event.set()
        status_label.config(text="⛔ 중단 요청됨...")

    # GUI 구성
    root = tk.Tk()
    root.title("🍎 macOS PDF OCR")

    tk.Label(root, text="PDF OCR을 위해 파일을 선택하세요.").pack(pady=10)
    tk.Button(root, text="📂 PDF 파일 선택", command=start_ocr, height=2, width=30).pack(pady=5)
    tk.Button(root, text="🛑 중단", command=stop_ocr, height=1, width=20).pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300)
    progress_bar.pack(pady=10)

    status_label = tk.Label(root, text="대기 중...")
    status_label.pack()

    root.geometry("400x250")
    root.mainloop()

if __name__ == "__main__":
    with contextlib.redirect_stderr(open(os.devnull, 'w')):
        run_gui()
