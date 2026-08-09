"""[테스트] 02_preprocess.py의 출퇴근 시간 분류 경계를 간단히 검증한다.

7~9시와 17~19시는 출퇴근 시간(True), 그 직전·직후 및 하루 양 끝 시간은
비출퇴근 시간(False)이어야 한다. 성공하면 ``ok``를 출력한다.
"""
import pandas as pd

RUSH_HOURS = set(range(7, 10)) | set(range(17, 20))

def classify(hour: int) -> bool:
    """주어진 시각이 프로젝트에서 정의한 출퇴근 시간인지 반환한다."""
    return hour in RUSH_HOURS

if __name__ == "__main__":
    # 출퇴근 시간 구간의 시작·중간·끝 경계를 모두 확인한다.
    assert classify(7) and classify(8) and classify(9)
    assert classify(17) and classify(18) and classify(19)
    # 구간 바로 바깥 시간이 잘못 포함되지 않는지 확인한다.
    assert not classify(6) and not classify(10) and not classify(16) and not classify(20)
    # 날짜 경계에 가까운 시간도 비출퇴근으로 유지되는지 확인한다.
    assert not classify(0) and not classify(23)
    print("ok")
