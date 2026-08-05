<script setup>
import { computed, ref, watch } from 'vue'
import { fetchNearbyAttractions } from '@/services/tourApi'
import { fetchNearbyHospitals, fetchNearbyPharmacies } from '@/services/hiraApi'
import { locateMyCity } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'

// 추가된 도시 중 하나 기준으로 근처 병원·약국·관광정보 조회
const configStore = useConfigStore()

const cityOptions = computed(() => configStore.trackedCities)
const selectedCity = ref(cityOptions.value[0] ?? null)
const isLocating = ref(false)

function selectCity(city) {
  selectedCity.value = city
}

// 현재 위치 조회
async function useMyLocation() {
  isLocating.value = true
  errorMessage.value = ''
  try {
    selectedCity.value = await locateMyCity()
  } catch (error) {
    console.error(error)
    errorMessage.value = '현재 위치를 확인하지 못했습니다.'
  } finally {
    isLocating.value = false
  }
}

const activeTab = ref('hospital') // 'hospital' | 'pharmacy' | 'tour'
const radius = ref(3000)

const results = ref([])
const isLoading = ref(false)
const errorMessage = ref('')

// 국내 좌표 범위 여부 확인 (공공데이터는 국내만 지원)
function isInKorea(city) {
  if (!city) return false
  const { latitude: lat, longitude: lon } = city
  return lat >= 33 && lat <= 39 && lon >= 124 && lon <= 132
}
const selectedCityInKorea = computed(() => isInKorea(selectedCity.value))

// 탭별 인증키 존재 여부
const hasHiraKey = Boolean(import.meta.env.VITE_HIRA_API_KEY)
const hasTourKey = Boolean(import.meta.env.VITE_TOUR_API_KEY)
const hasKeyForActiveTab = computed(() => (activeTab.value === 'tour' ? hasTourKey : hasHiraKey))

// 요청 경합 방지용 순번
let requestId = 0

async function loadResults() {
  const currentRequest = ++requestId
  if (!selectedCity.value) return
  results.value = []
  errorMessage.value = ''
  if (!isInKorea(selectedCity.value)) return
  isLoading.value = true
  try {
    let data
    if (activeTab.value === 'hospital') data = await fetchNearbyHospitals(selectedCity.value, radius.value)
    else if (activeTab.value === 'pharmacy') data = await fetchNearbyPharmacies(selectedCity.value, radius.value)
    else data = await fetchNearbyAttractions(selectedCity.value, { radius: radius.value })
    if (currentRequest !== requestId) return
    results.value = data
  } catch (error) {
    if (currentRequest !== requestId) return
    console.error(error)
    errorMessage.value = error.message?.includes('활용신청') ? error.message : '정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    if (currentRequest === requestId) isLoading.value = false
  }
}

watch([selectedCity, activeTab, radius], loadResults, { immediate: true })
</script>

<template>
  <main class="page-container">
    <p class="eyebrow">위치 기반 생활 정보</p>
    <h1>생활 정보</h1>
    <p>추가한 지역 근처의 병원·약국·관광정보를 찾아보세요.</p>

    <section class="living-info-box">
      <div class="living-info-toolbar">
        <!-- 도시 칩 (선택 시 .selected 강조) -->
        <div class="city-chip-row">
          <button v-for="city in cityOptions" :key="city.id" type="button" class="button" :class="{ selected: selectedCity?.id === city.id }" @click="selectCity(city)">
            {{ city.name }}
          </button>
          <button type="button" class="button" :disabled="isLocating" @click="useMyLocation">{{ isLocating ? '위치 확인 중…' : '📍 내 위치' }}</button>
        </div>
        <select v-model.number="radius" aria-label="검색 반경">
          <option :value="1000">1km 이내</option>
          <option :value="3000">3km 이내</option>
          <option :value="5000">5km 이내</option>
          <option :value="10000">10km 이내</option>
        </select>
      </div>

      <div class="trend-tabs" role="tablist" aria-label="생활 정보 종류">
        <button type="button" role="tab" :aria-selected="activeTab === 'hospital'" :class="{ active: activeTab === 'hospital' }" @click="activeTab = 'hospital'">🏥 병원</button>
        <button type="button" role="tab" :aria-selected="activeTab === 'pharmacy'" :class="{ active: activeTab === 'pharmacy' }" @click="activeTab = 'pharmacy'">💊 약국</button>
        <button type="button" role="tab" :aria-selected="activeTab === 'tour'" :class="{ active: activeTab === 'tour' }" @click="activeTab = 'tour'">🏞️ 관광정보</button>
      </div>

      <p v-if="!selectedCity" class="preview-empty">홈 화면에 추가한 도시가 없어요. 먼저 도시를 추가하거나 내 위치를 사용해 주세요.</p>
      <template v-else>
        <p v-if="!selectedCityInKorea" class="preview-empty">병원·약국·관광정보는 국내 공공데이터라 해외 지역은 지원하지 않아요. 국내 도시를 선택해 주세요.</p>
        <div v-else-if="isLoading" class="loading">불러오는 중입니다…</div>
        <p v-else-if="errorMessage" class="message error" role="alert">{{ errorMessage }} <button @click="loadResults">다시 시도</button></p>
        <p v-else-if="!hasKeyForActiveTab" class="preview-empty">
          {{ activeTab === 'tour' ? '한국관광공사 TourAPI' : '건강보험심사평가원 병원정보서비스/약국정보서비스' }} 인증키가 아직 없어요. .env에 키를 넣으면 실제 데이터가 나타납니다.
        </p>
        <p v-else-if="!results.length" class="preview-empty">이 반경 안에서는 결과를 찾지 못했어요. 반경을 넓혀 보세요.</p>
        <div v-else class="living-info-grid">
          <article v-for="(item, index) in results" :key="index" class="living-info-card">
            <template v-if="activeTab === 'tour'">
              <span class="living-info-icon">{{ item.icon }}</span>
              <div>
                <p class="living-info-type">{{ item.typeLabel }}</p>
                <strong>{{ item.title }}</strong>
                <p class="living-info-addr">{{ item.address }}</p>
              </div>
            </template>
            <template v-else>
              <span class="living-info-icon">{{ activeTab === 'hospital' ? '🏥' : '💊' }}</span>
              <div>
                <strong>{{ item.name }}</strong>
                <p class="living-info-addr">{{ item.address }}</p>
                <p v-if="item.phone" class="living-info-phone">{{ item.phone }}</p>
              </div>
            </template>
            <span v-if="item.distanceMeters" class="living-info-distance">{{ (item.distanceMeters / 1000).toFixed(1) }}km</span>
          </article>
        </div>
      </template>
    </section>
    <p class="source-note">병원·약국: 건강보험심사평가원 병원정보서비스·약국정보서비스 · 관광정보: 한국관광공사 TourAPI · 공공데이터포털(data.go.kr)</p>
  </main>
</template>
