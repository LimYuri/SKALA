<script setup>
import { computed, nextTick, ref } from 'vue'
import { cityFromQuery, cityToQuery, fetchWeather, searchCities, weatherCodeIcon, weatherCodeText } from '@/services/openWeatherApi'
import { useRoute, useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/configStore'
import { useHoverIndex } from '@/composables/useHover'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()
// 도시 카드/비교 표/검색 카드 호버 상태
const headerHover = useHoverIndex()
const rowHover = useHoverIndex()
const searchCardHover = useHoverIndex()
const defaults = [
  { id: 'seoul', name: '서울', country: '대한민국', admin: '서울', latitude: 37.566, longitude: 126.9784 },
  { id: 'busan', name: '부산', country: '대한민국', admin: '부산', latitude: 35.1796, longitude: 129.0756 },
]
const queryCities = [cityFromQuery(route.query, 'left'), cityFromQuery(route.query, 'right')]
const selectedCities = ref(queryCities.every(Boolean) ? queryCities : defaults)
const keywords = ref(['', ''])
const searchResults = ref([[], []])
const weatherResults = ref([])
const searchingSide = ref(-1)
const isLoading = ref(false)
const errorMessage = ref('')

const rows = computed(() =>
  weatherResults.value.length === 2
    ? [
        {
          label: '현재 기온',
          left: configStore.convertTemperature(weatherResults.value[0].current.temp),
          right: configStore.convertTemperature(weatherResults.value[1].current.temp),
          unit: configStore.unitSymbol,
        },
        {
          label: '체감 기온',
          left: configStore.convertTemperature(weatherResults.value[0].current.feels),
          right: configStore.convertTemperature(weatherResults.value[1].current.feels),
          unit: configStore.unitSymbol,
        },
        { label: '습도', left: weatherResults.value[0].current.humidity, right: weatherResults.value[1].current.humidity, unit: '%' },
        { label: '풍속', left: weatherResults.value[0].current.wind, right: weatherResults.value[1].current.wind, unit: ' km/h' },
        { label: '비 확률', left: weatherResults.value[0].daily[0].rain, right: weatherResults.value[1].daily[0].rain, unit: '%' },
      ]
    : [],
)

async function loadComparison() {
  errorMessage.value = ''
  isLoading.value = true
  try {
    weatherResults.value = await Promise.all(selectedCities.value.map(fetchWeather))
    router.replace({ query: { ...cityToQuery(selectedCities.value[0], 'left'), ...cityToQuery(selectedCities.value[1], 'right') } })
  } catch (error) {
    console.error(error)
    errorMessage.value = '비교 날씨를 불러오지 못했습니다. 다시 시도해 주세요.'
  } finally {
    isLoading.value = false
  }
}

async function searchSide(index) {
  if (!keywords.value[index].trim()) return
  const scrollTop = window.scrollY
  searchingSide.value = index
  errorMessage.value = ''
  try {
    searchResults.value[index] = await searchCities(keywords.value[index])
    if (!searchResults.value[index].length) errorMessage.value = '해당 지역을 지도에서 찾지 못했습니다.'
  } catch (error) {
    console.error(error)
    errorMessage.value = '지도 검색에 실패했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    searchingSide.value = -1
    await nextTick()
    window.scrollTo({ top: scrollTop, behavior: 'instant' })
  }
}

async function selectCity(index, city) {
  selectedCities.value[index] = city
  searchResults.value[index] = []
  keywords.value[index] = ''
  await loadComparison()
}

loadComparison()
</script>

<template>
  <main class="page-container narrow">
    <p class="eyebrow">SIDE BY SIDE</p>
    <h1>지역별 날씨 비교</h1>
    <p>각 검색창에서 지도 지역을 선택하면 두 지역의 실제 날씨를 바로 비교합니다.</p>

    <section class="compare-search-grid">
      <article
        v-for="(city, index) in selectedCities"
        :key="index"
        class="compare-search-card"
        :class="{ 'is-hovered': searchCardHover.isHovered(index) }"
        @mouseenter="searchCardHover.onEnter(index)"
        @mouseleave="searchCardHover.onLeave"
      >
        <small>{{ index === 0 ? '왼쪽 지역' : '오른쪽 지역' }}</small>
        <h2>{{ city.name }}</h2>
        <p>{{ city.country }} · {{ city.admin }}</p>
        <form @submit.prevent="searchSide(index)">
          <input v-model="keywords[index]" :aria-label="`${index === 0 ? '왼쪽' : '오른쪽'} 비교 지역 검색`" placeholder="지역명 입력 · 판교, 여수" />
          <button class="button primary" :disabled="searchingSide === index">{{ searchingSide === index ? '검색 중…' : '검색' }}</button>
        </form>
        <div v-if="searchResults[index].length" class="compare-search-results">
          <button v-for="place in searchResults[index]" :key="place.id" @click="selectCity(index, place)">
            <strong>{{ place.name }}</strong>
            <small>{{ place.country }} · {{ place.admin || place.displayAddress }}</small>
          </button>
        </div>
      </article>
    </section>

    <p v-if="errorMessage" class="message error">{{ errorMessage }} <button @click="loadComparison">다시 시도</button></p>
    <div v-if="isLoading" class="loading">두 지역의 날씨를 불러오는 중입니다…</div>
    <div v-else-if="weatherResults.length === 2" class="comparison">
      <header>
        <article
          v-for="(item, index) in weatherResults"
          :key="item.city.id"
          :class="{ 'is-hovered': headerHover.isHovered(index) }"
          @mouseenter="headerHover.onEnter(index)"
          @mouseleave="headerHover.onLeave"
        >
          <span>{{ weatherCodeIcon(item.current.code) }}</span>
          <h2>{{ item.city.name }}</h2>
          <p>{{ item.city.country }} · {{ weatherCodeText(item.current.code) }}</p>
          <strong>{{ configStore.formatTemperature(item.current.temp) }}</strong>
        </article>
      </header>
      <section
        v-for="(row, index) in rows"
        :key="row.label"
        class="compare-row"
        :class="{ 'is-hovered': rowHover.isHovered(index) }"
        @mouseenter="rowHover.onEnter(index)"
        @mouseleave="rowHover.onLeave"
      >
        <strong :class="{ winner: row.left > row.right }">{{ row.left }}{{ row.unit }}</strong
        ><span>{{ row.label }}</span
        ><strong :class="{ winner: row.right > row.left }">{{ row.right }}{{ row.unit }}</strong>
      </section>
      <p class="compare-help">강조 표시는 두 지역 중 수치가 더 큰 항목입니다.</p>
    </div>
  </main>
</template>
