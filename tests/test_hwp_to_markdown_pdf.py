import sys
import platform
import shutil
from pathlib import Path
import pypandoc
from matplotlib import font_manager

sys.path.insert(0, str(Path(__file__).parent.parent))

from helper_hwp import hwp_to_markdown

def get_available_korean_font() -> str:
    """시스템에서 사용 가능한 한글 폰트 반환
    
    Returns:
        str: 사용 가능한 폰트명
        
    Raises:
        SystemExit: 한글 폰트가 없을 경우
    """
    system = platform.system()
    
    # 우선순위별 폰트 목록 (유니코드 포괄 범위 우선)
    if system == "Windows":
        font_candidates = ["Arial Unicode MS", "NotoSans CJK KR", "Malgun Gothic", "맑은 고딕"]
        install_url = "https://github.com/notofonts/noto-cjk/releases (Noto Sans CJK)"
    else:  # Linux/macOS
        font_candidates = ["Noto Sans CJK KR", "NanumGothic"]
        install_url = "sudo apt install fonts-noto-cjk (Ubuntu/Debian)"
    
    # 시스템 폰트 목록 조회
    available_fonts = {f.name for f in font_manager.fontManager.ttflist}
    
    # 우선순위대로 확인
    for font in font_candidates:
        if font in available_fonts:
            return font
    
    # 폰트 없음
    print(f"\n[오류] 한글 폰트를 찾을 수 없습니다.")
    print(f"설치 필요: {', '.join(font_candidates[:2])}")
    print(f"설치 방법: {install_url}")
    sys.exit(1)

def test_hwp_to_markdown_pdf() -> None:
    """HWP → Markdown → PDF 변환 테스트 (한글 지원)"""
    # XeLaTeX 경로 확인 및 설정
    xelatex_path = shutil.which("xelatex")
    
    if not xelatex_path:
        # Windows MiKTeX 기본 경로 확인
        miktex_paths = [
            r"C:\Program Files\MiKTeX\miktex\bin\x64",
            r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64",
            r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64".format(Path.home().name),
        ]
        
        for miktex_bin in miktex_paths:
            if Path(miktex_bin).exists():
                import os
                os.environ["PATH"] = f"{miktex_bin};{os.environ['PATH']}"
                xelatex_path = shutil.which("xelatex")
                if xelatex_path:
                    print(f"XeLaTeX 경로 설정: {miktex_bin}")
                    break
        
        if not xelatex_path:
            print("\n[오류] XeLaTeX을 찾을 수 없습니다.")
            print("MiKTeX 설치: https://miktex.org/download")
            print("\n수동 PATH 추가:")
            print('  setx PATH "%PATH%;C:\\Program Files\\MiKTeX\\miktex\\bin\\x64"')
            sys.exit(1)
    
    hwp_path = Path(__file__).parent / "test.hwp"
    pdf_path = Path(__file__).parent / "test_hwp_to_markdown_pdf.pdf"
    md_path = Path(__file__).parent / "test_hwp_to_markdown_pdf.md"
    header_path = Path(__file__).parent / "test_hwp_to_markdown_pdf.tex"
    
    md_content = hwp_to_markdown(str(hwp_path))
    md_path.write_text(md_content, encoding="utf-8")
    
    mainfont = get_available_korean_font()
    bold_font = f"{mainfont} Bold" if "Malgun Gothic" in mainfont else mainfont
    print(f"사용 폰트: {mainfont}")
    
    # LaTeX 헤더 파일 생성
    header_content = (
        r"\usepackage{fontspec}" "\n"
        rf"\setmainfont{{{mainfont}}}[BoldFont={{{bold_font}}}]" "\n"
        rf"\setsansfont{{{mainfont}}}" "\n"
        rf"\setmonofont{{{mainfont}}}" "\n"
        r"\usepackage{xeCJK}" "\n"
        rf"\setCJKmainfont{{{mainfont}}}[BoldFont={{{bold_font}}}]" "\n"
        r"\usepackage[margin=1cm]{geometry}"
    )
    header_path.write_text(header_content, encoding="utf-8")
    
    pypandoc.convert_file(
        str(md_path),
        "pdf",
        outputfile=str(pdf_path),
        extra_args=[
            "--pdf-engine=xelatex",
            f"--include-in-header={header_path}",
        ],
    )
    
    print(f"변환 완료: {md_path}")
    print(f"변환 완료: {pdf_path}")

if __name__ == "__main__":
    test_hwp_to_markdown_pdf()