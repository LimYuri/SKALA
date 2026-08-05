<script setup>
import { computed, nextTick, onMounted, ref, watchEffect } from 'vue'
import BaseDashboardCard from '@/components/exercise/BaseDashboardCard.vue'
import RouterAxiosWeatherCard from '@/components/exercise/RouterAxiosWeatherCard.vue'
import { cityKey, cityToQuery, comfortScore, fetchWeather, locateMyCity, searchCities } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'
import { useRouter } from 'vue-router'
import { useHoverFlag, useHoverIndex } from '@/composables/useHover'

const configStore = useConfigStore()
const router = useRouter()
// 요약 카드 4개 중 호버 인덱스 추적
const summaryHover = useHoverIndex()
// 비교 트레이 호버 여부
const trayHover = useHoverFlag()

const weatherList = ref([])
const searchKeyword = ref('')
const localFilter = ref('')
const sortOrder = ref('default')
const searchResults = ref([])
const isLoading = ref(false)
const isSearching = ref(false)
const errorMessage = ref('')
const showFavoritesOnly = ref(false)
const selectedCityIds = ref([])
// 실패한 요청 재시도용 함수 저장
const lastRetry = ref(null)
// 검색창 포커스 시에만 최근 기록 드롭다운 표시
const isSearchFocused = ref(false)
const hasSearchHistory = computed(() => configStore.searchHistory.length > 0 || configStore.recentCities.length > 0)

// 현재 위치 기준 비 확률 (요약 카드용, 실패해도 조용히 무시)
const myLocationWeather = ref(null)
async function loadMyLocationWeather() {
  try {
    const city = await locateMyCity()
    myLocationWeather.value = await fetchWeather(city)
  } catch (error) {
    console.warn('내 위치 비 확률을 불러오지 못했습니다.', error)
  }
}

function retryLastAction() {
  const action = lastRetry.value
  errorMessage.value = ''
  lastRetry.value = null
  action?.()
}

function dismissError() {
  errorMessage.value = ''
  lastRetry.value = null
}

const displayedWeather = computed(() => {
  const keyword = localFilter.value.trim().toLowerCase()
  let result = keyword ? weatherList.value.filter(({ city }) => `${city.name} ${city.country}`.toLowerCase().includes(keyword)) : [...weatherList.value]
  if (showFavoritesOnly.value) result = result.filter(({ city }) => configStore.isFavorite(city.id))
  if (sortOrder.value === 'name') return result.sort((a, b) => a.city.name.localeCompare(b.city.name, 'ko'))
  if (sortOrder.value === 'temp-high') return result.sort((a, b) => b.current.temp - a.current.temp)
  if (sortOrder.value === 'rain-high') return result.sort((a, b) => b.daily[0].rain - a.daily[0].rain)
  // 쾌적지수 기준 정렬
  if (sortOrder.value === 'comfort-high') return result.sort((a, b) => comfortScore(b).score - comfortScore(a).score)
  return result
})

const summary = computed(() => {
  if (!displayedWeather.value.length) return { average: 0, hottest: '-', rainiest: '-' }
  const average = Math.round(displayedWeather.value.reduce((sum, item) => sum + item.current.temp, 0) / displayedWeather.value.length)
  const hottest = displayedWeather.value.reduce((a, b) => (a.current.temp > b.current.temp ? a : b))
  // 내 위치 날씨 우선, 없으면 목록 중 최고 비 확률로 대체
  const rainiestItem = myLocationWeather.value ?? displayedWeather.value.reduce((a, b) => (a.daily[0].rain > b.daily[0].rain ? a : b))
  const rainiest = `${rainiestItem.city.name} ${rainiestItem.daily[0].rain}%`
  return { average, hottest: hottest.city.name, rainiest }
})

const selectedWeather = computed(() => selectedCityIds.value.map((id) => weatherList.value.find((item) => item.city.id === id)).filter(Boolean))

function toggleCardSelection(cityId) {
  if (selectedCityIds.value.includes(cityId)) {
    selectedCityIds.value = selectedCityIds.value.filter((id) => id !== cityId)
    return
  }
  if (selectedCityIds.value.length >= 2) {
    // 전역 토스트로 안내
    configStore.showToast('비교할 도시는 두 곳까지만 선택할 수 있습니다.', 'warning')
    return
  }
  selectedCityIds.value = [...selectedCityIds.value, cityId]
}

function compareSelectedCities() {
  if (selectedWeather.value.length !== 2) return
  router.push({ name: 'weather-compare', query: { ...cityToQuery(selectedWeather.value[0].city, 'left'), ...cityToQuery(selectedWeather.value[1].city, 'right') } })
}

async function loadInitialWeather() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    // 추가된 도시들 날씨를 병렬 요청
    weatherList.value = await Promise.all(configStore.trackedCities.map(fetchWeather))
  } catch (error) {
    console.error(error)
    errorMessage.value = '날씨 데이터를 불러오지 못했습니다. 네트워크 상태를 확인하고 다시 시도해 주세요.'
    lastRetry.value = loadInitialWeather
  } finally {
    isLoading.value = false
  }
}

async function findCity() {
  if (!searchKeyword.value.trim()) return
  const scrollTop = window.scrollY
  isSearching.value = true
  errorMessage.value = ''
  isSearchFocused.value = false // 검색 실행 시 드롭다운 닫기
  configStore.recordSearch(searchKeyword.value)
  try {
    searchResults.value = await searchCities(searchKeyword.value.trim())
    if (!searchResults.value.length) errorMessage.value = '검색 결과가 없습니다. 도시 이름을 다시 확인해 주세요.'
  } catch (error) {
    console.error(error)
    errorMessage.value = '도시 검색에 실패했습니다. 잠시 후 다시 시도해 주세요.'
    lastRetry.value = findCity
  } finally {
    isSearching.value = false
    await nextTick()
    window.scrollTo({ top: scrollTop, behavior: 'instant' })
  }
}

// 최근 검색어 클릭 시 바로 검색 실행
function searchFromHistory(keyword) {
  searchKeyword.value = keyword
  findCity()
}

// 두 좌표 사이 거리(km) 계산
function haversineDistanceKm(a, b) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371
  const dLat = toRad(b.latitude - a.latitude)
  const dLon = toRad(b.longitude - a.longitude)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.latitude)) * Math.cos(toRad(b.latitude)) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}
function isSameCity(a, b) {
  if (cityKey(a) === cityKey(b)) return true
  if (a.name !== b.name) return false
  return haversineDistanceKm(a, b) < 2
}

// 이미 추가된 도시인지 확인 (배지·중복 방지용)
const isAlreadyTracked = (city) => weatherList.value.some((item) => isSameCity(item.city, city))

async function addCity(city) {
  const scrollTop = window.scrollY
  if (isAlreadyTracked(city)) {
    configStore.showToast('이미 추가된 도시입니다.', 'warning')
    return
  }
  isLoading.value = true
  try {
    const weather = await fetchWeather(city)
    weatherList.value.push(weather)
    configStore.addTrackedCity(weather.city)
    searchResults.value = []
    searchKeyword.value = ''
    configStore.showToast(`${city.name} 날씨를 추가했습니다.`, 'success')
  } catch (error) {
    console.error(error)
    errorMessage.value = '선택한 도시의 날씨를 불러오지 못했습니다.'
    lastRetry.value = () => addCity(city)
  } finally {
    isLoading.value = false
    await nextTick()
    window.scrollTo({ top: scrollTop, behavior: 'instant' })
  }
}

// 내 위치 날씨 추가
const isLocating = ref(false)
async function addMyLocation() {
  isLocating.value = true
  errorMessage.value = ''
  try {
    const city = await locateMyCity()
    await addCity(city)
  } catch (error) {
    console.error(error)
    errorMessage.value = error.message?.includes('denied') ? '위치 권한이 거부되었습니다. 브라우저 설정에서 위치 접근을 허용해 주세요.' : '현재 위치를 확인하지 못했습니다.'
  } finally {
    isLocating.value = false
  }
}

// 카드 드래그 순서 변경 (기본 정렬·필터 없음 상태에서만 허용)
const canReorder = computed(() => sortOrder.value === 'default' && !localFilter.value.trim() && !showFavoritesOnly.value)
const draggedCityId = ref(null)
const dragOverCityId = ref(null)

function onCardDragStart(cityId, event) {
  if (!canReorder.value) return
  draggedCityId.value = cityId
  event.dataTransfer.effectAllowed = 'move'
}
function onCardDragOver(cityId, event) {
  if (!canReorder.value || !draggedCityId.value) return
  event.preventDefault()
  dragOverCityId.value = cityId
}
function onCardDrop(cityId) {
  if (canReorder.value && draggedCityId.value && draggedCityId.value !== cityId) {
    const ids = weatherList.value.map((item) => item.city.id)
    const from = ids.indexOf(draggedCityId.value)
    const to = ids.indexOf(cityId)
    if (from !== -1 && to !== -1) {
      ids.splice(to, 0, ids.splice(from, 1)[0])
      weatherList.value = ids.map((id) => weatherList.value.find((item) => item.city.id === id))
      configStore.reorderTrackedCities(ids)
    }
  }
  draggedCityId.value = null
  dragOverCityId.value = null
}
function onCardDragEnd() {
  draggedCityId.value = null
  dragOverCityId.value = null
}

// 도시 삭제 (목록 + 추적 목록에서 함께 제거)
function removeCity(cityId) {
  weatherList.value = weatherList.value.filter((item) => item.city.id !== cityId)
  configStore.removeTrackedCity(cityId)
  selectedCityIds.value = selectedCityIds.value.filter((id) => id !== cityId)
}

function updateFilter(event) {
  const scrollTop = window.scrollY
  localFilter.value = event.target.value
  nextTick(() => window.scrollTo({ top: scrollTop, behavior: 'instant' }))
}

function updateSort(event) {
  const scrollTop = window.scrollY
  sortOrder.value = event.target.value
  nextTick(() => window.scrollTo({ top: scrollTop, behavior: 'instant' }))
}

function resetListConditions() {
  localFilter.value = ''
  sortOrder.value = 'default'
  showFavoritesOnly.value = false
}

// 검색어를 새로 입력하면 이전 에러 메시지 초기화
watchEffect(() => {
  if (searchKeyword.value) errorMessage.value = ''
})

onMounted(() => {
  loadInitialWeather()
  loadMyLocationWeather()
})
</script>

<template>
  <main class="page-container">
    <!-- 검색 히어로 영역 -->
    <BaseDashboardCard class="hero">
      <template #eyebrow>지금 날씨 확인하기</template>
      <template #title>오늘의 날씨</template>
      <p>궁금한 지역을 찾아 오늘 날씨를 확인해 보세요. 카드 두 개를 고르면 바로 비교할 수도 있습니다.</p>
      <form class="city-search" @submit.prevent="findCity">
        <div class="city-search-input-wrap">
          <input v-model="searchKeyword" aria-label="도시 검색" placeholder="도시 이름 입력 · 제주, 판교, 부산진구" @focus="isSearchFocused = true" @blur="isSearchFocused = false" />
          <!-- 최근 검색어 + 최근 조회 도시 드롭다운 -->
          <div v-if="isSearchFocused && hasSearchHistory" class="search-history-dropdown">
            <button type="button" class="search-history-close" aria-label="최근 기록 닫기" @mousedown.prevent="isSearchFocused = false">✕</button>
            <div v-if="configStore.searchHistory.length" class="search-history-group">
              <span class="search-history-label">최근 검색어</span>
              <div class="search-history-chips">
                <span v-for="keyword in configStore.searchHistory" :key="keyword" class="search-history-chip">
                  <button type="button" class="search-history-chip-label" @mousedown.prevent="searchFromHistory(keyword)">🔍 {{ keyword }}</button>
                  <button type="button" class="search-history-chip-remove" aria-label="검색어 삭제" @mousedown.prevent.stop="configStore.removeSearchHistoryItem(keyword)">✕</button>
                </span>
              </div>
            </div>
            <div v-if="configStore.recentCities.length" class="search-history-group">
              <span class="search-history-label">최근 조회 도시</span>
              <div class="search-history-chips">
                <span v-for="item in configStore.recentCities" :key="item.id" class="search-history-chip">
                  <RouterLink class="search-history-chip-label" :to="{ name: 'weather-detail', params: { cityId: item.id }, query: cityToQuery(item) }" @mousedown.prevent="isSearchFocused = false">
                    {{ item.name }}
                  </RouterLink>
                  <button type="button" class="search-history-chip-remove" aria-label="최근 조회 도시 삭제" @mousedown.prevent.stop="configStore.removeRecentCity(item.id)">✕</button>
                </span>
              </div>
            </div>
          </div>
        </div>
        <button class="button primary" :disabled="isSearching">{{ isSearching ? '검색 중…' : '도시 검색' }}</button>
        <!-- 현재 위치로 날씨 추가 -->
        <button type="button" class="button" :disabled="isLocating" @click="addMyLocation">{{ isLocating ? '위치 확인 중…' : '📍 내 위치 날씨' }}</button>
      </form>
      <div v-if="searchResults.length" class="search-results">
        <button v-for="city in searchResults" :key="city.id" class="search-result-item" :class="{ 'is-added': isAlreadyTracked(city) }" @click="addCity(city)">
          <strong>{{ city.name }}<span v-if="isAlreadyTracked(city)" class="already-added-badge">이미 추가됨</span></strong>
          <small>{{ city.country }}{{ city.countryCode ? ` (${city.countryCode})` : '' }} · {{ city.admin || '지역 정보 없음' }}</small>
          <small>{{ city.type }} · {{ city.displayAddress || `${Number(city.latitude).toFixed(4)}, ${Number(city.longitude).toFixed(4)}` }}</small>
        </button>
      </div>
    </BaseDashboardCard>

    <!-- 에러 배너, 재시도 가능하면 버튼 표시 -->
    <p v-if="errorMessage" class="message error" role="alert">
      {{ errorMessage }}
      <button v-if="lastRetry" @click="retryLastAction">다시 시도</button>
      <button @click="dismissError">닫기</button>
    </p>
    <section class="summary-grid">
      <article :class="{ 'is-hovered': summaryHover.isHovered(0) }" @mouseenter="summaryHover.onEnter(0)" @mouseleave="summaryHover.onLeave">
        <small>표시 지역</small><strong>{{ displayedWeather.length }}</strong>
      </article>
      <article :class="{ 'is-hovered': summaryHover.isHovered(1) }" @mouseenter="summaryHover.onEnter(1)" @mouseleave="summaryHover.onLeave">
        <small>평균 기온</small><strong>{{ configStore.formatTemperature(summary.average) }}</strong>
      </article>
      <article :class="{ 'is-hovered': summaryHover.isHovered(2) }" @mouseenter="summaryHover.onEnter(2)" @mouseleave="summaryHover.onLeave">
        <small>가장 더운 지역</small><strong>{{ summary.hottest }}</strong>
      </article>
      <article :class="{ 'is-hovered': summaryHover.isHovered(3) }" @mouseenter="summaryHover.onEnter(3)" @mouseleave="summaryHover.onLeave">
        <small>오늘 비 확률</small><strong>{{ summary.rainiest }}</strong>
      </article>
    </section>

    <section class="toolbar">
      <input :value="localFilter" aria-label="추가된 도시 안에서 검색" placeholder="추가된 도시 필터" @input="updateFilter" />
      <select :value="sortOrder" aria-label="정렬 기준" @change="updateSort">
        <option value="default">추가한 순서</option>
        <option value="name">도시 이름순</option>
        <option value="temp-high">기온 높은순</option>
        <option value="rain-high">비 확률 높은순</option>
        <option value="comfort-high">쾌적지수 높은순</option>
      </select>
      <button class="button" :disabled="isLoading" @click="loadInitialWeather">새로고침</button>
      <!-- 새로고침 버튼과 동일한 스타일 -->
      <button type="button" class="button" :class="{ favorite: showFavoritesOnly }" @click="showFavoritesOnly = !showFavoritesOnly">
        {{ showFavoritesOnly ? '★ 즐겨찾기만' : '☆ 전체 지역' }}
      </button>
    </section>

    <div v-if="isLoading && !weatherList.length" class="loading">실시간 날씨를 불러오는 중입니다…</div>
    <template v-else>
      <!-- 기본 정렬·필터 없음 상태에서만 드래그 가능 -->
      <p v-if="!canReorder && displayedWeather.length > 1" class="reorder-hint">💡 카드 순서를 직접 바꾸려면 정렬을 "추가한 순서"로, 필터를 초기화해 주세요.</p>
      <section class="weather-grid">
        <div
          v-for="weather in displayedWeather"
          :key="weather.city.id"
          class="card-drag-wrap"
          :class="{ 'is-dragging': draggedCityId === weather.city.id, 'is-drag-over': dragOverCityId === weather.city.id && draggedCityId !== weather.city.id, 'can-reorder': canReorder }"
          :draggable="canReorder"
          @dragstart="onCardDragStart(weather.city.id, $event)"
          @dragover="onCardDragOver(weather.city.id, $event)"
          @drop="onCardDrop(weather.city.id)"
          @dragend="onCardDragEnd"
        >
          <RouterAxiosWeatherCard :weather="weather" :selected="selectedCityIds.includes(weather.city.id)" @toggle-select="toggleCardSelection" @remove="removeCity" />
        </div>
      </section>
    </template>
    <aside v-if="selectedWeather.length" class="compare-tray" :class="{ 'is-hovered': trayHover.isHovered }" aria-live="polite" @mouseenter="trayHover.onEnter" @mouseleave="trayHover.onLeave">
      <div>
        <strong>비교할 도시 {{ selectedWeather.length }}/2</strong>
        <span>{{ selectedWeather.map((item) => item.city.name).join(' · ') }}</span>
      </div>
      <button class="text-button" @click="selectedCityIds = []">선택 취소</button>
      <button class="button primary" :disabled="selectedWeather.length !== 2" @click="compareSelectedCities">선택한 도시 비교</button>
    </aside>
    <!-- 조건에 맞는 지역 없음 -->
    <section v-if="!isLoading && displayedWeather.length === 0" class="empty-state" role="status">
      <a-empty description="해당 조건에 맞는 지역이 없습니다.">
        <a-button type="primary" @click="resetListConditions">조건 초기화</a-button>
      </a-empty>
    </section>
    <p class="source-note">지역 검색: © OpenStreetMap contributors · 날씨: OpenWeatherMap · Axios + 발급받은 API Key로 요청</p>
  </main>
</template>
