# SKALA-Vue 날씨 과제

Vue 3(Composition API) + Vue Router + Pinia + Axios로 만든 실시간 날씨 대시보드. 국내 지역(시/도 · 시/군/구) 날씨 조회, 지역 비교, 전국 지도, 그리고 병원·약국·관광정보를 보여주는 "생활 정보" 탭까지 포함하였다.

## 주요 기능

- 오늘 날씨: 관심 지역을 검색해서 홈 화면에 추가하고, 실시간 기온·체감온도·습도·풍속을 확인 가능함
- 지역 검색: 시/도 → 시/군/구 순서로 골라도 되고, 도시 이름으로 바로 검색해도 됨 (전국 229개 시/군/구 지원)
- 지역 비교: 두 지역을 골라 날씨를 나란히 비교 가능함
- 전국 날씨: 주요 도시별 기온을 지도 위에서 한눈에 확인 가능함
- 생활 정보: 홈 화면에 추가한 지역 근처의 병원·약국·관광정보를 공공데이터로 조회함(국내 지역만 지원)
- 다크모드, 즐겨찾기, 최근 검색 기록, 온도 단위(℃/℉) 전환

## 기술 스택

Vue 3 · Vue Router · Pinia · Axios · ant-design-vue · Leaflet · Vite


## 환경변수 (필수)

`.env` 파일에는 실제 API 키가 들어가기 때문에 보안상 저장소에 올리지 않았다.

| 변수명 | 값/발급처 | 비고 |
| --- | --- | --- |
| `VITE_OPENWEATHER_API_KEY` | OpenWeatherMap| 실시간 날씨 |
| `VITE_OPENWEATHER_API_URL` | `https://api.openweathermap.org` |
| `VITE_KMA_API_KEY` | 공공데이터포털 기상청_기상특보 조회서비스 | 상세 페이지 공식 기상특보 |
| `VITE_HIRA_API_KEY` | 공공데이터포털 건강보험심사평가원 병원정보서비스 | 생활 정보 · 병원 탭 |
| `VITE_TOUR_API_KEY` | 공공데이터포털 한국관광공사 TourAPI| 생활 정보 · 관광정보 탭 |
| `VITE_RADAR_API_URL` | `https://api.rainviewer.com` | 강수 레이더 |


## 폴더 구조

```
src/
├── components/exercise/  # 실습용 컴포넌트 (카드, 토글, 배너 등)
├── data/                 # 전국 시/도-시/군/구 지역 데이터
├── router/               # 라우트 정의
├── services/             # OpenWeatherMap · 공공데이터 API 연동
├── stores/               # Pinia 스토어 (설정, 즐겨찾기, 검색 기록 등)
└── views/                # 페이지 단위 컴포넌트
```
