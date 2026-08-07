"""
================================================================================
프로그램명   : [실습 2] 파일 I/O, 예외 처리, Pydantic 검증 파이프라인
작성자       : 판교 7반 임유리
작성일       : 2026-08-06
설명         : Python_Practice2_Data.json(Sales, 100건)을 안전하게 읽고,
               Pydantic v2 SalesRecord 모델로 각 행을 검증한다. 정상/오류를
               분리해 각각 CSV·JSON으로 저장하고, 저장한 CSV를 다시 읽어
               건수를 재검증한다.
               * 함수명은 safe_load_csv를 그대로 유지하되 내부 구현은
                 json.load()로 변경했다.
               * 실제 데이터 100건은 정상 데이터라 검증 실패 행이 자연적으로 존재하지 않는다
                 (전수 확인 결과 month/region 공백, amount<=0 케이스 0건). 
                 따라서 "실제 100건 파이프라인"과 별도로 "ValidationError 예외 처리 시연"을 위한 
                 검증용 이상값 3종을 독립적으로 테스트하여 오류 처리 로직이 정상 동작함을 증명한다.
내용 :            safe_load_csv를 json.load() 기반으로 변경, 검증 오류 시연 로직 추가
================================================================================
"""

import json
import logging # 시스템의 상태, 에러, 디버깅 정보를 로그 레벨별로 체계적으로 관리하고 출력함
from pathlib import Path # 파일 시스템의 경로를 문자열이 아닌 객체로 다룸
from typing import Any # 모든 자료형을 허용하고 싶을 때 사용함

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator # 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") # 파이썬 로깅 시스템의 출력 형태를 지정함
logger = logging.getLogger(__name__) # 현재 코드가 실행되는 파일(모듈)의 이름을 기반으로 독립적인 로거 객체를 생성함

BASE_DIR = Path(__file__).parent 
DATA_FILE = BASE_DIR / "Python_Practice2_Data.json"
VALID_CSV = BASE_DIR / "valid_sales.csv"
ERRORS_JSON = BASE_DIR / "invalid_sales.json"


# --------------------------------------------------------------------------
# 1) 예외 처리 + 파일 읽기
# --------------------------------------------------------------------------
def safe_load_csv(file_path: Path) -> list[dict] | None:
    """데이터 파일을 안전하게 읽는다.

    함수명은 원 실습 명세의 safe_load_csv를 그대로 사용하지만, 실제
    데이터 파일이 JSON이므로 내부적으로 json.load()를 사용한다.
    - 파일이 없으면 None 반환 + logger.error
    - 성공 시 dict 리스트 반환 + logger.info
    - finally에서 '로딩 종료' 출력
    """
    try: # 프로그램 실행 중 발생할 수 있는 에러(예외)를 안전하게 처리하고, 에러 발생 여부와 상관없이 무조건 특정 코드를 실행하도록 보장함
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("데이터 로드 성공: %s (%d건)", file_path.name, len(data))
        return data
    except FileNotFoundError:
        logger.error("파일을 찾을 수 없습니다: %s", file_path)
        return None
    except json.JSONDecodeError as e:
        logger.error("JSON 파싱 오류: %s", e)
        return None
    finally:
        print("로딩 종료")


# --------------------------------------------------------------------------
# 2) Pydantic v2 스키마 정의
# --------------------------------------------------------------------------
class SalesRecord(BaseModel):
    """month·region은 비어있으면 안 되고, amount는 0 초과, category는 선택값."""

    model_config = ConfigDict(str_strip_whitespace=True) # 입력되는 모든 문자열 데이터의 앞뒤 공백을 자동으로 제거한 뒤 검증 및 저장하도록 처리하는 기능

    month: str = Field(min_length=1) # Field : 모델 내부의 각 변수가 가저야 하는 규칙, 기본값, 제약 조건을 정의함
    region: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str | None = None # 이 필드는 선택사항임(None)

    @field_validator("category", mode="before") # 커스텀 벨리레이터 선언 : 카테고리 필드의 데이터 검증 및 전처리를 수행함
    @classmethod # pydantic v2의 데코레이터 구조상, 클래스 메서드 형태로 첫 번째 인자에 cls를 받도록 설계되어 있어 필수적으로 함께 선언해야 함
    def blank_category_to_none(cls, value: Any) -> str | None: # 입력값이 None이거나 공백만 가득한 문자열일 때 이를 안전하게 None을 정리하고, 값이 있을때는 앞뒤 공백을 자른 문자열을 반환함
        if value is None:
            return None
        text = str(value).strip()
        return text or None


# --------------------------------------------------------------------------
# 3) 검증 파이프라인 (valid / errors 분리)
# --------------------------------------------------------------------------
def validate_records(raw_data: list[dict]) -> tuple[list[SalesRecord], list[dict]]: # 대용량 리스트 데이터를 일괄 처리할 때 발생하는 일부 에러 데이터로 인해 전체 시스템이 멈추는 현상을 방지함
    """raw_data를 순회하며 SalesRecord로 변환. 성공→valid, 실패→errors."""
    valid: list[SalesRecord] = []
    errors: list[dict] = []
    for idx, row in enumerate(raw_data, start=1): # 몇번째 행에서 에러가 났는지
        try:
            valid.append(SalesRecord.model_validate(row)) # Pydantic v2의 내부 파싱 엔진을 호출해, 앞서 정의했던 문자열 공백 제거, 빈 카테고리 변환, 금액 제약 조건이 동시에 실행됨
        except ValidationError as e:
            logger.error("검증 실패 - row=%d, error=%s", idx, e.errors(include_url=False)) # e.errors() : 기본적으로 에러 메시지에 상세 공식 문서 URL 링크를 자동으로 첨부하는데, False를 통해 불필요한 링크 텍스트를 제거하고, 오직 에러 원인만 딕셔너리 리스트로 추출함
            errors.append({"row": idx, "error": e.errors(include_url=False)})
    return valid, errors


def demo_validation_errors() -> None: # 예외 처리 로직이 명세대로 완벽하게 작동하는 검증하기 위한 데모
    """실제 100건 데이터에는 오류 행이 없으므로, ValidationError 처리 로직이
    정상 동작함을 별도의 이상값 3종으로 시연한다(체크포인트: "ValidationError
    발생 시 오류 내용 출력")."""
    bad_cases = [
        {"month": "", "region": "서울", "amount": 1000, "category": "전자"},  # month 공백
        {"month": "2024-01", "region": "", "amount": 1000, "category": "전자"},  # region 공백
        {"month": "2024-01", "region": "서울", "amount": 0, "category": "전자"},  # amount<=0
    ]
    print("\n=== ValidationError 예외 처리 시연 (실제 데이터에 없는 이상값 3종) ===")
    for case in bad_cases: # 고의로 발생시킨 예외를 안전하게 포착하여 에러 메세지의 전말을 상세히 출력함
        try:
            SalesRecord.model_validate(case)
        except ValidationError as e:
            print(f"[예상된 오류] {case} ->")
            print(e)


# --------------------------------------------------------------------------
# 4) 결과 파일 저장 + 재로딩 확인
# --------------------------------------------------------------------------
def save_results(valid: list[SalesRecord], errors: list[dict]) -> None: # 각각의 목적에 맞는 파일 포맷으로 분류하여 안전하게 영구 저장함
    """valid 레코드는 CSV로, errors는 JSON으로 저장."""
    import csv

    with open(VALID_CSV, "w", encoding="utf-8", newline="") as f: 
        writer = csv.DictWriter(f, fieldnames=["month", "region", "amount", "category"])
        writer.writeheader()
        for record in valid:
            writer.writerow(record.model_dump()) # 객체를 딕셔너리로 변환 후 csv.DictWriter를 통해 CSV로 저장함

    with open(ERRORS_JSON, "w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)

    logger.info("저장 완료: %s (%d건), %s (%d건)", VALID_CSV.name, len(valid), ERRORS_JSON.name, len(errors))


def reload_and_verify(expected_count: int) -> list[dict]: # 디스크에 저장된 결과 파일을 다시 읽어와서 데이터 누락이나 훼손이 없는지 확인함
    """저장된 valid_sales.csv를 다시 읽어 건수를 검증한다."""
    import csv

    with open(VALID_CSV, encoding="utf-8", newline="") as f:
        reloaded = list(csv.DictReader(f)) # csv.DictReader : CSV 파일 자동으로 파싱해서 각 행을 딕셔너리로 변환함
    assert len(reloaded) == expected_count, f"재로딩 건수 불일치: {len(reloaded)} != {expected_count}" # 기록되는 과정에서 유실되지 않고 정확하게 일치하는지 검증함
    logger.info("재로딩 검증 통과: len(reloaded)=%d", len(reloaded)) # 정상 통과 시 타임스탬프와 함께 검증 기록을 남김
    return reloaded


def main() -> None:
    try:
        # 존재하지 않는 파일 -> None 반환 확인
        assert safe_load_csv(BASE_DIR / "no_such_file.json") is None
        logger.info("safe_load_csv(존재하지 않는 파일) -> None 확인 완료")

        # 실제 데이터 로드
        raw_data = safe_load_csv(DATA_FILE)
        if raw_data is None:
            raise RuntimeError("Python_Practice2_Data.json 로드 실패")
        print(f"raw_data {len(raw_data)}건 로드")

        # 검증 파이프라인 (실제 데이터: 오류 없이 전량 통과하는 게 정상)
        valid, errors = validate_records(raw_data)
        print(f"valid: {len(valid)}건 / errors: {len(errors)}건")
        assert len(valid) == 100 # 실제 데이터에 결함이 없음을 전제로, 조건을 강제하여 데이터 왜곡이나 유실이 없는지 체크포인트
        assert len(errors) == 0
        logger.info("실제 데이터 100건 전량 검증 통과 확인")

        # ValidationError 예외 처리 로직 자체는 별도로 시연
        demo_validation_errors()

        # 저장 + 재로딩 확인
        save_results(valid, errors)
        reload_and_verify(expected_count=len(valid))

    except AssertionError as e: # 내가 의도한 검증 조건이 깨졌을 때
        logger.error("검증 단계 실패: %s", e)
    except Exception as e: # 시스템이나 네트워크 문제 등으로 발생한 돌발 에러
        logger.exception("실행 중 예기치 않은 오류 발생: %s", e) # 단순 에러 메시지 + 상세 에러 트레이스백 모두 기록
    finally:
        logger.info("실습 2 종료")


if __name__ == "__main__":
    main()



# 실제 데이터가 모두 정상이라 오류가 없어서, 실습에서 요구하는 ValidationError 처리를 위해 demo_validation_errors()가 필요하다고 느꼈다
# field_validator("category", mode="before") + @classmethod 조합 — mode="before"을 사용할때, Pydantic이 타입 검사/제약 조건을 적용하기 전에 원본 값을 정규화해야 했는데 이 과정이 어려웠던 것 같다.
# 그리고 try 안에 return이 있어도 finally가 반드시 실행된다는 것을 확인했다
# 평소 예외처리, 오류 처리에 대해서는 많은 관심이 없었고 자주 사용해보지도 않았는데, 이번 실습을 통해 잘 코딩 시 잘 이용할 수 있을 것 같다는 생각이 들었다.
# 특히 로그나 기록 같은것을 통해 눈으로 직접 확인할 수 있는 점이 좋았던 것 같다