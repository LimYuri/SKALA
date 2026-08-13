# SKALA 4기 과제 제출물 모음

날짜/수업 순서대로 최종 제출했던 과제들을 정리했습니다.

## 07-14 · 팀빌딩, Git 이해/활용
- `index.html`, `newsletter.html` — Git/GitHub 실습용 첫 정적 페이지 (skala-intro 저장소에서 이관)

## 07-15 · Prompt 설계와 Context
- `임유리.md` — "국내 프리미엄 육아용품 시장 분석"을 주제로, 초기 프롬프트 → 한계점 분석 → Context/Framework 엔지니어링 → 최종 비교까지 4단계로 진행한 프롬프트 설계 실습 (조원: 김광현, 임채현, 박서연, 임유리)

## 07-16, 07-20 · 데이터 분석 개요 및 기초통계
- `과제2_BikeSharing_수요예측_회귀분석.ipynb` — UCI Bike Sharing Dataset으로 날씨·계절·요일 등 환경 요인 기반 일별 자전거 대여량(cnt)을 예측하는 다중선형회귀 개인 과제 (문제정의→EDA/전처리→모델구축→결과해석 4단계)
- `7반6조.ipynb` — 위와 같은 주제의 7반 6조 팀 과제 (팀원: 김광현·임유리·임채현)

## 07-23, 07-24 · HTML, CSS, JavaScript
- `index.html`, `style.css`, `app.js` — "중고차 목록 관리" CRUD 실습 과제 (P231). 차량 정보를 등록·조회·수정·삭제하는 폼 기반 웹 페이지

## 07-27 ~ 07-30 · 스마트 데이터 이해 및 활용 (PostgreSQL)
- `day01_쿼리_임유리.sql` — day01 실습 쿼리 제출본
- `day02_쿼리_임유리.sql` — day02 실습 쿼리 제출본
- `day02_캡쳐_임유리.pdf` — day02 실행 결과 캡쳐
- `day03_쿼리_임유리.sql` — day03 인덱스 튜닝 10문제 (EXPLAIN ANALYZE 기반 개선 전/후 비교, 검증 완료본)
- `day04_쿼리_임유리_final.sql` — day04 프로시저/함수 8문제 최종본 (PostgreSQL 18 재실행 검증 완료, 선행 스키마 파일과 함께 실행 필요)

## 07-31 ~ 08-05 · Front-framework: Vue.js
Vue 3(Composition API) + Vue Router + Pinia + Axios 기반 실시간 날씨 대시보드. 국내 지역 날씨 조회/비교, 전국 지도, 병원·약국·관광정보 "생활 정보" 탭 포함. API 키(`.env`)는 보안상 제외하고 제출.

**views/** (라우터로 연결되는 페이지)
- `WeatherExploreView.vue` — 홈 화면. 관심 지역을 검색해서 추가하고 오늘 날씨 카드들을 보여줌
- `WeatherForecastView.vue` — 도시 상세 예보 (실시간 기온·체감온도·습도·풍속, 일출/일몰 타임라인)
- `WeatherCompareView.vue` — 두 지역 날씨 나란히 비교
- `SearchView.vue` — 시/도 → 시/군/구 선택 또는 도시 이름으로 지역 검색 (전국 229개 시/군/구)
- `NationwideWeatherView.vue` — 주요 도시 기온을 지도 위에서 한눈에 보기
- `NearbyInfoView.vue` — 관심 지역 근처 병원·약국·관광정보 (생활 정보)
- `NotFoundView.vue` — 404 페이지

**components/exercise/** (재사용 컴포넌트)
- `BaseDashboardCard.vue` — 카드 바깥 틀 (슬롯 기반 재사용 컴포넌트)
- `RouterAxiosWeatherCard.vue` — 홈 화면의 도시별 날씨 카드 (라우터 링크 + axios 데이터 연동)
- `TodayWeatherInsights.vue` — 오늘 날씨 상세 지표(체감온도, 습도, 풍향 등) 표시
- `TodayPrepTabs.vue` — 알림 / 옷차림·음식 추천 탭
- `ClothingFoodTips.vue` — 체감온도 기반 옷차림·음식 추천 카드
- `SevereWeatherBanner.vue` — 자체 판단 주의보 + 기상청 공식 특보(KMA) 배너
- `SunTimeline.vue` — 낮 경과율을 해 아이콘 위치로 표시하는 타임라인
- `WeatherRadar.vue` — Leaflet 기반 강수 레이더 지도
- `ThemeToggler.vue` — 라이트/다크 모드 토글
- `UnitToggler.vue` — 온도 단위(℃/℉) 전환
- `ToastHost.vue` — 전역 토스트 알림 표시

**services/** (외부 API 연동)
- `openWeatherApi.js` — OpenWeatherMap 날씨 조회, 옷차림/음식 추천, 대기질·풍향 텍스트 변환 등 핵심 로직
- `weatherApi.js` — RainViewer 강수 레이더 API (키 불필요)
- `weatherAlertApi.js` — 기상청 기상특보 조회서비스 (공공데이터포털)
- `hiraApi.js` — 건강보험심사평가원 병원·약국 정보서비스 (공공데이터포털)
- `tourApi.js` — 한국관광공사 TourAPI 관광정보 (공공데이터포털)

**기타**
- `stores/configStore.js` — Pinia 스토어. 관심 지역, 다크모드, 온도 단위, 즐겨찾기·최근 검색 기록 등 전역 상태 관리
- `composables/useHover.js` — 카드/리스트에 마우스를 올렸을 때 강조 효과를 주는 컴포저블
- `data/koreaRegions.js` — 전국 시/도 → 시/군/구 2단계 지역 좌표 데이터
- `router/index.js` — 위 views를 경로에 연결하는 라우트 정의
- `App.vue`, `main.js` — 앱 진입점 및 루트 레이아웃

## 08-06 ~ 08-07 · Python 데이터 분석 및 AI 모델링

### Day 1 종합실습 (Python 데이터 파이프라인)
Open-Meteo(서울 3일 시간대별 기온·강수확률), Countries.dev(대한민국 국가 정보), ip-api(IP 위치 정보) 3개 API를 `httpx` + `asyncio.gather()`로 동시에 수집하고, Pydantic v2로 타입·범위를 검증한 뒤 CSV/Parquet로 저장하며 성능을 비교하는 파이프라인.

- `app/config.py` — API 주소·타임아웃·저장 경로 설정
- `app/models.py` — Pydantic v2 검증 모델 (Open-Meteo/Countries.dev/ip-api 응답)
- `app/api_client.py` — httpx+asyncio.gather() 기반 3개 API 동시 수집 클라이언트
- `app/pipeline.py` — 필드 추출·Pydantic 검증·정제 파이프라인 로직
- `app/storage.py` — CSV/Parquet 저장 및 쓰기·읽기 성능 측정 로직
- `app/main.py` — 실행 진입점 (실행 로그·검증 오류 흐름 포함)
- `tests/` — pytest 테스트 11건 (api_client/models/pipeline/storage)
- `data/output/seoul_weather_report.csv`, `.parquet` — 검증 통과 데이터
- `data/output/performance_result.json` — CSV/Parquet 쓰기·읽기 시간, 파일 크기 비교 결과
- `data/output/raw_api_snapshot.json` — 3개 API 원본 응답 스냅샷
- `판교_7반_임유리_day1종합실습_실행결과.pdf` — 실행 결과 보고서 (프로젝트 개요/실행결과/성능비교/테스트·git 이력/전체 코드/본인 소감 포함)

### practice/ (같은 수업에서 진행한 개별 실습)
- `practice1.py` — [심화 실습 1] 자료구조 집계·컴프리헨션·제너레이터. Sales 데이터를 리스트/딕셔너리 컴프리헨션으로 필터링·지역별 집계하고, Counter·defaultdict로 그룹화, 제너레이터로 메모리 사용량 비교, 월·카테고리 기준 상위 3개 조합 추출
- `practice2.py` — [실습 2] 파일 I/O, 예외 처리, Pydantic 검증 파이프라인. Sales 데이터를 안전하게 읽어 Pydantic v2로 검증, 정상/오류 데이터를 CSV·JSON으로 분리 저장 후 재검증, ValidationError 예외 처리 시연 포함
  - (실행에 필요한 `Python_Practice1_Data.json`, `Python_Practice2_Data.json` 원본 데이터 파일은 별도로 받지 못해 포함되어 있지 않습니다)
- `practice3.py` — [실습 3] Pandas EDA · Polars Lazy · DuckDB SQL 비교. sales_100k.csv(100만 행)를 region/category/amount 기준으로 정제(결측 22,860건 제거) 후 IQR 이상치 제거(956,363행 유지), 세 가지 방식으로 동일 집계를 구현해 결과 일치 여부(assert_frame_equal)와 실행 시간(timeit)을 비교 (Polars가 Pandas보다 약 15배 빠름을 확인)
- `practice4.py` — [실습 4] 데이터 분석 및 AI 모델링 종합 실습. practice3이 저장한 정제 데이터를 입력으로 ① 2×2 EDA 대시보드(히스토그램+KDE, 박스플롯, 월별 라인, 상관 히트맵) ② t-test(서울 vs 부산)·카이제곱 독립성 검정 ③ ColumnTransformer+Ridge Pipeline 학습·평가·저장·재로딩 ④ Plotly Express 인터랙티브 막대 차트(.html) 저장까지 수행
  - (practice3이 생성하는 `sales_100k_cleaned.csv`, `region_category_agg.csv` 입력 파일과 `sales_100k.csv` 원본은 포함되어 있지 않습니다)

### 종합실습2_NYC-Taxi-분석 (Day 2 종합실습)
NYC Yellow Taxi 운행 데이터를 Pandas·Polars로 정제하고(1899만 행 → 정제 906만 행) 시간대별 운행 특성을 통계적으로 분석한 뒤 sklearn Pipeline으로 총요금을 예측하는 End-to-End 프로젝트. 팀원: 임채현·임유리·김광현 (개인 제출본). 최초 분석(출퇴근 vs 비출퇴근 단순비교) → 1차 개선(Cohen's d 효과크기 추가) → 2차 개선(5개 시간대 밴드 분석)까지 3단계로 개선하며 진행. 회귀모델 성능: RMSE 4.132 · MAE 2.430 · R² 0.9333. 원천/정제 데이터(CSV 875MB, Parquet 136MB)는 용량 문제로 제외.

- `main.py` — 전체 파이프라인 실행 진입점 (다운로드→전처리→분석→모델링→시각화→보고서 생성)
- `scripts/01_download_data.py` — NYC TLC 원천 Parquet 다운로드
- `scripts/02_preprocess.py` — Pandas·Polars 정제 및 교차 검증 (결측치/중복/자료형/평균·합계 비교)
- `scripts/03_analysis.py` — 기술통계·상관분석·최초 Welch t-test
- `scripts/04_model.py` — StandardScaler+LinearRegression sklearn Pipeline 학습·저장
- `scripts/05_report.py`, `07_report_v2.py`, `09_report_v3.py` — 단계별(v1/v2/v3) 보고서 생성
- `scripts/06_analysis_v2.py` — 속도·마일당 요금 분석, Cohen's d 효과크기 추가
- `scripts/08_analysis_v3.py` — 5개 시간대 밴드(낮/심야 등) 분석
- `scripts/10_plotly_chart.py` — Plotly Express 인터랙티브 시간대별 차트 생성
- `scripts/11_report_jinja.py` — Jinja2 기반 최종 종합 보고서(`report.md`) 자동 생성
- `outputs/figures/` — Seaborn 정적 시각화 PNG 5개 + Plotly 인터랙티브 HTML 1개
- `outputs/tables/` — 기술통계·상관행렬·t-test·회귀 평가지표·Pandas/Polars 비교 결과 CSV/JSON
- `models/total_amount_regression_pipeline.joblib` — 저장된 회귀 Pipeline 모델
- `report.md`, `report_v1.md`, `report_v2.md`, `report_v3.md` — 단계별 분석 보고서
- `판교_7반_임유리_day2종합실습_제출보고서.pdf` — 개인 제출 보고서 (팀 공통 분석 + 본인 기여 부분 포함)

## 08-10 ~ 08-14 · Java & Spring Boot

**01.java/** — Java 기초~심화 (1~3일차 오전)
- `01.snippet` ~ `05.for` — 변수/자료형, 네이밍 규칙, 클래스와 객체, 제어문(if/switch/while/for)
- `06.exception` — 예외 처리
- `07.oop` — 객체지향 (Calculator, stock/stock-abstract/stock-interface/stock-poly 예제)
- `08.collection`, `09.generic` — Collection Type, Generic Type
- `10.lambda`, `11.stream` — Lambda Expression, Stream API
- `12.reflection`, `13.annotation` — Reflection, Annotation (class/field/method/parameter)
- `14.pattern` — 객체 생성 패턴
- `15.soild` — SOLID 원칙 (OCP/LSP/DIP)
- `16.socket` — 네트워크 기초, Socket, Simple HTTP

**02.spring/01.training-code/** — REST API와 Spring Boot (3일차 오후~5일차)
- `01.start` — Spring Boot 프로젝트 시작 (myapp, myapp-dto)
- `02.layer` — 컴포넌트 스캔, Controller/Service/Repository 계층 구조
- `03.lombak` — Lombok
- `04.properties` — properties 설정 관리
- `05.di`, `06.simple-ioc-container` — IoC/DI, 직접 구현한 간단한 IoC 컨테이너
- `07.proxy`, `08.aop` — Proxy 패턴, AOP
- `09.valid` — 입력값 검증
- `10.async` — 비동기 처리(Async)
- `11.jpa`, `12.jpa-relation`, `13.jpa-transaction` — JPA, 엔티티 관계 매핑, Entity Manager/Transactional
- `14.openapi` — REST API 문서화
- `15.actuator` — Spring Actuator
- `16.execise` — 종합 실습
- `17.http-api-server` — HTTP API 서버 구현
