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

# Vision 프레임워크의 텍스트 인식 결과를 처리합니다.
# 각 인식 결과(observation)에서 가장 가능성이 높은 텍스트 후보를 추출하여
# 하나의 문자열로 합칩니다.
def handle_results(results):
    texts = []
    for observation in results:
        top_candidate = observation.topCandidates_(1).firstObject()
        if top_candidate:
            texts.append(top_candidate.string())
    return "\n".join(texts)

# 지정된 이미지 파일 경로에서 텍스트를 인식합니다.
# macOS Vision 프레임워크를 사용하여 OCR을 수행합니다.
#
# Args:
#   image_path (Path): OCR을 수행할 이미지 파일의 경로입니다.
#
# Returns:
#   str: 인식된 텍스트입니다. OCR에 실패하면 에러 메시지를 반환합니다.
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

# PDF 파일을 텍스트로 변환하고 진행 상황을 GUI에 표시합니다.
#
# PDF의 각 페이지를 이미지로 변환한 후 OCR을 수행합니다.
# 중간에 중단 이벤트(stop_event)를 감지하여 처리를 중단할 수 있습니다.
# OCR 결과는 지정된 출력 파일에 저장되며, 완료 후 자동으로 해당 파일을 엽니다.
#
# Args:
#   pdf_path (str): 변환할 PDF 파일의 경로입니다.
#   output_txt (str): OCR 결과를 저장할 텍스트 파일의 경로입니다.
#   progress_var (tk.DoubleVar): 진행률을 업데이트할 Tkinter 변수입니다.
#   progress_bar (ttk.Progressbar): 진행률을 표시할 Tkinter Progressbar 위젯입니다.
#   status_label (tk.Label): 현재 상태를 표시할 Tkinter Label 위젯입니다.
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

# 애플리케이션의 메인 GUI를 설정하고 실행합니다.
#
# GUI에는 PDF 파일 선택 버튼, OCR 중단 버튼, 진행 표시줄,
# 그리고 현재 상태를 나타내는 레이블이 포함됩니다.
def run_gui():
    # 'PDF 파일 선택' 버튼을 클릭했을 때 호출됩니다.
    # 파일 대화상자를 열어 PDF 파일을 선택받고,
    # OCR 작업을 별도의 스레드에서 시작합니다.
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

    # '중단' 버튼을 클릭했을 때 호출됩니다.
    # OCR 중단 이벤트를 설정하여 진행 중인 OCR 작업을 중단하도록 요청하고,
    # 상태 레이블을 업데이트합니다.
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

# 스크립트가 직접 실행될 때 호출되는 메인 블록입니다.
# GUI를 실행하며, Vision 프레임워크 관련 상세 오류 메시지가 터미널에 출력되는 것을 방지하기 위해
# 표준 에러(stderr)를 /dev/null로 리디렉션합니다.
if __name__ == "__main__":
    with contextlib.redirect_stderr(open(os.devnull, 'w')):
        run_gui()
