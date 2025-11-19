"""hwp_to_txt 함수 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from helper_hwp import hwp_to_txt

def test_hwp_to_txt():
    hwp_path = Path(__file__).parent / "test.hwp"
    txt_path = Path(__file__).parent / "test_hwp_to_txt.txt"
    
    # HWP에서 텍스트 추출
    text = hwp_to_txt(str(hwp_path))
    
    # 파일로 저장
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"변환 완료: {txt_path}")
    print(f"\n=== 출력 내용 ({len(text)} 글자) ===")
    print(text[:500])

if __name__ == "__main__":
    test_hwp_to_txt()
