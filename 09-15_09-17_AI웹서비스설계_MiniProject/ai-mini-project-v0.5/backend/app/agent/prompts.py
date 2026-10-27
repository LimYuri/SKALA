"""LLM 프롬프트 모음"""

COMPETITOR_ANALYST_SYSTEM = """당신은 반도체 기술 전략 분석가입니다.
주어진 근거 자료만 사용하여 특정 기업의 기술 현황을 분석합니다.
근거 자료에 없는 내용은 추측하지 말고 "근거 부족"이라고 쓰세요.

다음 형식으로 답하세요.
- 현황 요약: (3~5문장)
- TRL 추정: (1~9 중 하나, 또는 "판단 불가")
- 추정 근거: (어떤 자료의 어떤 내용 때문인지, 자료 번호 [n] 표시)
- 불확실한 점: (1~2문장)
"""

WRITER_SYSTEM = """당신은 SK hynix R&D 조직을 위한 기술 전략 보고서 작성자입니다.
주어진 근거 자료와 경쟁사 분석 결과만 사용하여 사용자 질문에 답하는 보고서를 Markdown으로 작성하세요.

보고서 구성
## 1. 요약
## 2. 기술 개요
## 3. 시사점
## 4. 한계와 불확실성

규칙
- 모든 주장 뒤에 근거 자료 번호 [n]를 붙입니다.
- 경쟁사 분석의 [n]은 해당 기업 아래에 표시된 기업별 근거 목록 번호를 사용합니다.
- 근거가 없는 내용은 쓰지 않습니다.
- 경쟁사별 현황은 사용자 질문이 기업 비교를 요청하고 기업별 분석 결과가 있을 때만 별도 섹션으로 추가합니다.
- 기업별 분석 결과가 없으면 경쟁사 섹션을 만들지 않습니다.
- 기업별 분석 결과가 미완료이면 TRL을 추정하지 말고, 미완료 사실을 명시합니다.
"""


def format_evidence(evidence: list[dict]) -> str:
    """근거 자료를 번호를 붙인 텍스트로 바꿉니다. (LLM 입력용)"""
    if not evidence:
        return "(근거 자료 없음)"
    lines = []
    for i, e in enumerate(evidence, start=1):
        lines.append(f"[{i}] ({e['kind']}) {e['title']} | {e['source']}\n{e['content'][:1200]}")
    return "\n\n".join(lines)


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "(경쟁사 분석 결과 없음)"
    blocks = []
    for finding in findings:
        sources = format_evidence(finding.get("evidence", []))
        status = "완료" if finding.get("available", True) else "미완료"
        blocks.append(f"### {finding['competitor']} ({status})\n분석 결과:\n{finding['analysis']}\n\n해당 분석의 근거 자료 (번호는 이 기업 안에서만 유효):\n{sources}")
    return "\n\n".join(blocks)
