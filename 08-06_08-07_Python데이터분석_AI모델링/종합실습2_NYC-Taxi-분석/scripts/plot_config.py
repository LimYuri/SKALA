"""Windows·macOS·Linux에서 한글 차트를 위한 공통 Matplotlib 설정을 제공한다.

각 분석 스크립트가 이 함수를 호출하면 운영체제별 한글 폰트를 우선순위대로
선택하고, 사용할 수 없는 경우 Matplotlib 기본 폰트로 안전하게 대체한다.
"""
import platform

import matplotlib.pyplot as plt
from matplotlib import font_manager


def configure_matplotlib() -> str:
    """사용 가능한 한글 폰트를 적용하고 실제 선택된 폰트 이름을 반환한다."""
    # 운영체제에 기본 포함될 가능성이 높은 폰트부터 후보 순서를 정한다.
    candidates = {
        "Windows": ("Malgun Gothic", "Noto Sans CJK KR", "NanumGothic"),
        "Darwin": ("AppleGothic", "Noto Sans CJK KR", "NanumGothic"),
        "Linux": ("Noto Sans CJK KR", "NanumGothic", "Malgun Gothic"),
    }.get(platform.system(), ("Noto Sans CJK KR", "NanumGothic", "Malgun Gothic"))

    # 현재 실행 환경에 실제로 설치된 폰트만 대상으로 선택한다.
    available = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((name for name in candidates if name in available), "DejaVu Sans")
    plt.rcParams["font.family"] = selected
    # 음수 기호가 한글 폰트에서 네모 상자로 깨지는 현상을 방지한다.
    plt.rcParams["axes.unicode_minus"] = False
    return selected
