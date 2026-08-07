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

## 08-06 · Day 1 종합실습 (Python 데이터 파이프라인)
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
