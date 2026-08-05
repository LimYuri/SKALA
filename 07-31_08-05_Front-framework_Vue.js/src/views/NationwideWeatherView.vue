<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { cityToQuery, fetchWeather, weatherCodeIcon } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'

const configStore = useConfigStore()

// 전국 지도에 표시할 주요 도시 10곳
const MAJOR_CITIES = [
  { id: 'kr-seoul', name: '서울', country: '대한민국', admin: '서울', latitude: 37.5665, longitude: 126.978 },
  { id: 'kr-incheon', name: '인천', country: '대한민국', admin: '인천', latitude: 37.4563, longitude: 126.7052 },
  { id: 'kr-suwon', name: '수원', country: '대한민국', admin: '경기', latitude: 37.2636, longitude: 127.0286 },
  { id: 'kr-gangneung', name: '강릉', country: '대한민국', admin: '강원', latitude: 37.7519, longitude: 128.8761 },
  { id: 'kr-daejeon', name: '대전', country: '대한민국', admin: '대전', latitude: 36.3504, longitude: 127.3845 },
  { id: 'kr-daegu', name: '대구', country: '대한민국', admin: '대구', latitude: 35.8714, longitude: 128.6014 },
  { id: 'kr-gwangju', name: '광주', country: '대한민국', admin: '광주', latitude: 35.1595, longitude: 126.8526 },
  { id: 'kr-ulsan', name: '울산', country: '대한민국', admin: '울산', latitude: 35.5384, longitude: 129.3114 },
  { id: 'kr-busan', name: '부산', country: '대한민국', admin: '부산', latitude: 35.1796, longitude: 129.0756 },
  { id: 'kr-jeju', name: '제주', country: '대한민국', admin: '제주', latitude: 33.4996, longitude: 126.5312 },
]

const mapElement = ref(null)
const cityWeather = ref([]) // [{ city, weather }]
const isLoading = ref(true)
const errorMessage = ref('')
let map
const markers = []

// 가장 덥고 추운 곳 요약
const summary = computed(() => {
  if (!cityWeather.value.length) return null
  const hottest = cityWeather.value.reduce((a, b) => (a.weather.current.temp > b.weather.current.temp ? a : b))
  const coldest = cityWeather.value.reduce((a, b) => (a.weather.current.temp < b.weather.current.temp ? a : b))
  return { hottest, coldest }
})

// 도시 이름 + 기온 말풍선 마커 생성
function buildMarkerIcon(item) {
  const html = `<div class="city-temp-pin"><span>${weatherCodeIcon(item.weather.current.code)}</span><strong>${configStore.formatTemperature(item.weather.current.temp)}</strong><small>${item.city.name}</small></div>`
  return L.divIcon({ html, className: 'city-temp-pin-wrapper', iconSize: [70, 54], iconAnchor: [35, 54] })
}

function renderMarkers() {
  markers.forEach((marker) => marker.remove())
  markers.length = 0
  cityWeather.value.forEach((item) => {
    const marker = L.marker([item.city.latitude, item.city.longitude], { icon: buildMarkerIcon(item) }).addTo(map)
    markers.push(marker)
  })
}

async function loadNationwide() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    // 병렬 요청, 개별 실패는 무시하고 성공한 도시만 남김
    const results = await Promise.all(
      MAJOR_CITIES.map((city) =>
        fetchWeather(city)
          .then((weather) => ({ city, weather }))
          .catch(() => null),
      ),
    )
    cityWeather.value = results.filter(Boolean)
    if (!cityWeather.value.length) errorMessage.value = '주요 도시 날씨를 하나도 불러오지 못했습니다.'
    await nextTick()
    renderMarkers()
  } catch (error) {
    console.error(error)
    errorMessage.value = '전국 날씨를 불러오지 못했습니다.'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  map = L.map(mapElement.value, { zoomControl: true, scrollWheelZoom: false }).setView([36.2, 127.8], 6.6)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: 'Map © OpenStreetMap contributors' }).addTo(map)
  await loadNationwide()
})
onBeforeUnmount(() => map?.remove())
</script>

<template>
  <main class="page-container">
    <p class="eyebrow">지도로 한눈에</p>
    <h1>전국 날씨</h1>
    <p>주요 도시 10곳의 실시간 기온을 지도 위에서 한눈에 비교해 보세요.</p>

    <section v-if="summary" class="summary-grid">
      <article>
        <small>표시 도시</small><strong>{{ cityWeather.length }}</strong>
      </article>
      <article>
        <small>가장 더운 곳</small><strong>{{ summary.hottest.city.name }} {{ configStore.formatTemperature(summary.hottest.weather.current.temp) }}</strong>
      </article>
      <article>
        <small>가장 추운 곳</small><strong>{{ summary.coldest.city.name }} {{ configStore.formatTemperature(summary.coldest.weather.current.temp) }}</strong>
      </article>
    </section>

    <p v-if="errorMessage" class="message error" role="alert">{{ errorMessage }} <button @click="loadNationwide">다시 시도</button></p>
    <div v-if="isLoading" class="loading">주요 도시 날씨를 불러오는 중입니다…</div>

    <section class="nationwide-map-section">
      <div ref="mapElement" class="nationwide-map" aria-label="전국 주요 도시 기온 지도"></div>
    </section>

    <section class="nationwide-grid">
      <RouterLink v-for="item in cityWeather" :key="item.city.id" class="nationwide-city-card" :to="{ name: 'weather-detail', params: { cityId: item.city.id }, query: cityToQuery(item.city) }">
        <span>{{ weatherCodeIcon(item.weather.current.code) }}</span>
        <strong>{{ item.city.name }}</strong>
        <span>{{ configStore.formatTemperature(item.weather.current.temp) }}</span>
      </RouterLink>
    </section>
    <p class="source-note">날씨: OpenWeatherMap · 지도: OpenStreetMap · 좌표가 고정된 10개 주요 도시만 표시합니다.</p>
  </main>
</template>
