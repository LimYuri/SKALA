<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { REGIONS, REGION_SHORT_NAMES } from '@/data/koreaRegions'
import { cityToQuery, fetchWeather, searchCities, weatherCodeIcon } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'
import { useRouter } from 'vue-router'

const configStore = useConfigStore()
const router = useRouter()

// 시/도 탭 기본값 (서울)
const selectedRegion = ref(REGIONS[0])
const selectedDistrict = ref(null)

const searchKeyword = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const searchError = ref('')

const previewWeather = ref(null)
const isLoadingPreview = ref(false)
const previewError = ref('')

const mapElement = ref(null)
let map
let marker

// 시/도 탭 변경
function selectRegion(region) {
  selectedRegion.value = region
}

// (시/도, 시/군/구) -> 공통 도시 객체 변환
function toCity(region, district) {
  return {
    name: district.name,
    country: '대한민국',
    admin: region.name,
    latitude: district.lat,
    longitude: district.lon,
  }
}

async function loadPreview(city) {
  isLoadingPreview.value = true
  previewError.value = ''
  previewWeather.value = null
  try {
    previewWeather.value = await fetchWeather(city)
  } catch (error) {
    console.error(error)
    previewError.value = '날씨 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    isLoadingPreview.value = false
    await nextTick()
    updateMap(city)
  }
}

// 시/군/구 선택 시 미리보기 + 지도 로드
function selectDistrict(district) {
  selectedDistrict.value = district
  loadPreview(toCity(selectedRegion.value, district))
}

// 선택 칩 표시용 라벨
const selectionLabel = computed(() => {
  if (!previewWeather.value) return ''
  const city = previewWeather.value.city
  return city.admin ? `${city.admin} ${city.name}` : city.name
})

// 선택 해제
function clearSelection() {
  selectedDistrict.value = null
  previewWeather.value = null
  previewError.value = ''
  if (marker) {
    marker.remove()
    marker = null
  }
}

// 지도 중심·마커 이동
function updateMap(city) {
  if (!map) return
  map.setView([city.latitude, city.longitude], 11)
  if (marker) marker.remove()
  marker = L.marker([city.latitude, city.longitude]).addTo(map)
}

// 이름으로 바로 검색
async function runSearch() {
  if (!searchKeyword.value.trim()) return
  isSearching.value = true
  searchError.value = ''
  try {
    searchResults.value = await searchCities(searchKeyword.value.trim())
    if (!searchResults.value.length) searchError.value = '검색 결과가 없습니다. 이름을 다시 확인해 주세요.'
  } catch (error) {
    console.error(error)
    searchError.value = '검색에 실패했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    isSearching.value = false
  }
}

// 검색 결과 선택
function selectSearchResult(city) {
  selectedDistrict.value = null
  loadPreview(city)
}

// 미리보기 도시를 홈 화면에 추가
function addToHome() {
  if (!previewWeather.value) return
  configStore.addTrackedCity(previewWeather.value.city)
  configStore.showToast(`${previewWeather.value.city.name}을(를) 오늘 날씨에 추가했습니다.`, 'success')
}

function goToDetail() {
  if (!previewWeather.value) return
  router.push({ name: 'weather-detail', params: { cityId: previewWeather.value.city.id }, query: cityToQuery(previewWeather.value.city) })
}

onMounted(() => {
  // 전국이 보이는 축소 배율로 시작, 선택 시 확대
  map = L.map(mapElement.value, { zoomControl: true, scrollWheelZoom: false }).setView([36.2, 127.8], 6.6)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: 'Map © OpenStreetMap contributors' }).addTo(map)
})
onBeforeUnmount(() => map?.remove())
</script>

<template>
  <main class="page-container">
    <p class="eyebrow">전국에서 지역 찾기</p>
    <h1>지역 검색</h1>
    <p>시/도 → 시/군/구 순서로 골라도 되고, 도시 이름을 바로 검색해도 됩니다. 오른쪽에서 날씨를 미리 보고 바로 메인에 추가할 수 있어요.</p>

    <div class="search-layout">
      <section class="search-panel">
        <form class="city-search" @submit.prevent="runSearch">
          <input v-model="searchKeyword" aria-label="도시 이름으로 검색" placeholder="도시 이름으로 바로 검색 · 전주, 통영, 춘천" />
          <button class="button primary" :disabled="isSearching">{{ isSearching ? '검색 중…' : '검색' }}</button>
        </form>
        <p v-if="searchError" class="message error" role="alert">{{ searchError }}</p>
        <div v-if="searchResults.length" class="search-results">
          <button v-for="city in searchResults" :key="city.id" @click="selectSearchResult(city)">
            <strong>{{ city.name }}</strong>
            <small>{{ city.country }} · {{ city.admin || '지역 정보 없음' }}</small>
          </button>
        </div>

        <div class="region-picker">
          <p class="hierarchy-label">지역 선택 · 시/도 → 시/군/구</p>
          <!-- 선택된 지역 칩 -->
          <div v-if="previewWeather" class="selected-chips">
            <button type="button" class="selected-chip" @click="clearSelection">{{ selectionLabel }} ✕</button>
          </div>
          <div class="picker-body">
            <div class="province-tabs" role="tablist" aria-label="시/도 선택">
              <button
                v-for="region in REGIONS"
                :key="region.name"
                type="button"
                role="tab"
                :aria-selected="selectedRegion.name === region.name"
                class="province-tab"
                :class="{ active: selectedRegion.name === region.name }"
                @click="selectRegion(region)"
              >
                {{ REGION_SHORT_NAMES[region.name] ?? region.name }}
              </button>
            </div>
            <div class="district-list">
              <button
                v-for="district in selectedRegion.districts"
                :key="district.name"
                type="button"
                class="district-row"
                :class="{ active: selectedDistrict?.name === district.name }"
                @click="selectDistrict(district)"
              >
                {{ district.name }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <aside class="search-preview">
        <div ref="mapElement" class="search-map" aria-label="선택한 지역 지도"></div>

        <div v-if="isLoadingPreview" class="loading">날씨를 불러오는 중입니다…</div>
        <p v-else-if="previewError" class="message error" role="alert">{{ previewError }}</p>
        <div v-else-if="previewWeather" class="preview-card">
          <div class="preview-card-head">
            <span>{{ weatherCodeIcon(previewWeather.current.code) }}</span>
            <div>
              <strong>{{ previewWeather.city.name }}</strong>
              <small>{{ previewWeather.city.admin }} {{ previewWeather.city.country }}</small>
            </div>
          </div>
          <p class="preview-temp">{{ configStore.formatTemperature(previewWeather.current.temp) }}</p>
          <p class="preview-desc">체감 {{ configStore.formatTemperature(previewWeather.current.feels) }} · 오늘 강수확률 {{ previewWeather.daily[0].rain }}%</p>
          <div class="preview-actions">
            <a-button type="primary" :disabled="configStore.isTracked(previewWeather.city.id)" @click="addToHome">
              {{ configStore.isTracked(previewWeather.city.id) ? '✅ 이미 추가됨' : '메인에 추가' }}
            </a-button>
            <button class="button" @click="goToDetail">상세보기</button>
          </div>
        </div>
        <p v-else class="preview-empty">왼쪽에서 지역을 고르면<br />여기서 날씨 미리보기와 위치를 볼 수 있어요.</p>
      </aside>
    </div>
    <p class="source-note">지역 목록: 전국 17개 시/도의 시/군/구 229곳 · 날씨: OpenWeatherMap · 지도: OpenStreetMap</p>
  </main>
</template>
