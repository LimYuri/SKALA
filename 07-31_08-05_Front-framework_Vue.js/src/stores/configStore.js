// Pinia Setup Store 문법
import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'

// 기본 3개 도시 (국내 지역만)
const DEFAULT_CITIES = [
  { id: '1835848', name: '서울', country: '대한민국', admin: '서울', latitude: 37.566, longitude: 126.9784 },
  { id: '1838524', name: '부산', country: '대한민국', admin: '부산', latitude: 35.1796, longitude: 129.0756 },
  { id: '1846266', name: '제주', country: '대한민국', admin: '제주', latitude: 33.4996, longitude: 126.5312 },
]

export const useConfigStore = defineStore('config', () => {
  // 온도 단위, localStorage에서 복원
  const unit = ref(localStorage.getItem('weather-unit') ?? 'celsius')

  // 즐겨찾기 도시 id 목록
  const favoriteCityIds = ref(JSON.parse(localStorage.getItem('weather-favorites') ?? '[]'))

  // 추가한 도시 목록 (홈 화면 표시용)
  const trackedCities = ref(JSON.parse(localStorage.getItem('weather-tracked-cities') ?? 'null') ?? DEFAULT_CITIES)

  // 다크모드 여부
  const theme = ref(localStorage.getItem('weather-theme') ?? 'light')

  // 최근 조회한 도시 (최대 5개)
  const recentCities = ref(JSON.parse(localStorage.getItem('weather-recent-cities') ?? '[]'))

  // 도시별 마지막 조회 기온 기록 (전일 대비 비교용)
  const tempHistory = ref(JSON.parse(localStorage.getItem('weather-temp-history') ?? '{}'))

  // 최근 검색어 (최대 8개)
  const searchHistory = ref(JSON.parse(localStorage.getItem('weather-search-history') ?? '[]'))

  // 단위 기호 (℃ / ℉)
  const unitSymbol = computed(() => {
    return unit.value === 'celsius' ? '℃' : '℉'
  })

  // 단위 토글
  function toggleUnit() {
    unit.value = unit.value === 'celsius' ? 'fahrenheit' : 'celsius'
  }

  // 테마 토글
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 섭씨 -> 화씨 변환
  const convertTemperature = (celsius) => (unit.value === 'celsius' ? Math.round(celsius) : Math.round((celsius * 9) / 5 + 32))
  // 변환값 + 단위 기호 문자열
  const formatTemperature = (celsius) => `${convertTemperature(celsius)}${unitSymbol.value}`

  // 즐겨찾기 여부 확인/토글
  const isFavorite = (cityId) => favoriteCityIds.value.includes(cityId)
  function toggleFavorite(cityId) {
    favoriteCityIds.value = isFavorite(cityId) ? favoriteCityIds.value.filter((id) => id !== cityId) : [...favoriteCityIds.value, cityId]
  }

  // 추가된 도시 여부 확인/추가/삭제
  const isTracked = (cityId) => trackedCities.value.some((city) => city.id === cityId)
  function addTrackedCity(city) {
    if (isTracked(city.id)) return
    trackedCities.value = [...trackedCities.value, city]
  }
  function removeTrackedCity(cityId) {
    trackedCities.value = trackedCities.value.filter((city) => city.id !== cityId)
  }

  // 드래그 순서 변경 반영
  function reorderTrackedCities(orderedIds) {
    const byId = new Map(trackedCities.value.map((city) => [city.id, city]))
    trackedCities.value = orderedIds.map((id) => byId.get(id)).filter(Boolean)
  }

  // 최근 조회 도시 갱신 (맨 앞으로, 최대 5개)
  function visitCity(city) {
    const withoutDuplicate = recentCities.value.filter((item) => item.id !== city.id)
    recentCities.value = [city, ...withoutDuplicate].slice(0, 5)
  }
  // 최근 조회 도시 삭제
  function removeRecentCity(cityId) {
    recentCities.value = recentCities.value.filter((item) => item.id !== cityId)
  }

  // 기온 기록 후 전일 대비 차이 반환
  function recordTempAndGetDiff(cityId, date, temp) {
    const previous = tempHistory.value[cityId]
    tempHistory.value = { ...tempHistory.value, [cityId]: { date, temp } }
    if (!previous || previous.date === date) return null
    const diff = temp - previous.temp
    const daysBetween = Math.round((new Date(date) - new Date(previous.date)) / (1000 * 60 * 60 * 24))
    return { diff, isExactlyYesterday: daysBetween === 1, previousDate: previous.date }
  }

  // 검색어 기록 (맨 앞으로, 최대 8개)
  function recordSearch(keyword) {
    const trimmed = keyword.trim()
    if (!trimmed) return
    const withoutDuplicate = searchHistory.value.filter((item) => item.toLowerCase() !== trimmed.toLowerCase())
    searchHistory.value = [trimmed, ...withoutDuplicate].slice(0, 8)
  }
  // 검색어 기록 삭제
  function removeSearchHistoryItem(keyword) {
    searchHistory.value = searchHistory.value.filter((item) => item !== keyword)
  }

  // 전역 토스트 알림
  const toast = ref(null) // { type: 'success' | 'warning', text: string } | null
  let toastTimer = null
  function showToast(text, type = 'success') {
    toast.value = { type, text }
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => (toast.value = null), 2400)
  }

  // 상태 변경 시 localStorage 동기화
  watch(unit, (value) => localStorage.setItem('weather-unit', value))
  // 테마는 html data-theme 속성도 함께 반영
  watch(
    theme,
    (value) => {
      localStorage.setItem('weather-theme', value)
      document.documentElement.dataset.theme = value
    },
    { immediate: true },
  )
  watch(favoriteCityIds, (value) => localStorage.setItem('weather-favorites', JSON.stringify(value)), { deep: true })
  watch(trackedCities, (value) => localStorage.setItem('weather-tracked-cities', JSON.stringify(value)), { deep: true })
  watch(recentCities, (value) => localStorage.setItem('weather-recent-cities', JSON.stringify(value)), { deep: true })
  watch(tempHistory, (value) => localStorage.setItem('weather-temp-history', JSON.stringify(value)), { deep: true })
  watch(searchHistory, (value) => localStorage.setItem('weather-search-history', JSON.stringify(value)), { deep: true })

  return {
    unit,
    unitSymbol,
    toggleUnit,
    favoriteCityIds,
    trackedCities,
    convertTemperature,
    formatTemperature,
    isFavorite,
    toggleFavorite,
    isTracked,
    addTrackedCity,
    removeTrackedCity,
    reorderTrackedCities,
    toast,
    showToast,
    theme,
    toggleTheme,
    recentCities,
    visitCity,
    removeRecentCity,
    recordTempAndGetDiff,
    searchHistory,
    recordSearch,
    removeSearchHistoryItem,
  }
})
