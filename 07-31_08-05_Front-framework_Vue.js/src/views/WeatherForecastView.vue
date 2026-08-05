<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cityFromQuery, fetchWeather, weatherCodeIcon, weatherCodeText } from '@/services/openWeatherApi'
import TodayWeatherInsights from '@/components/exercise/TodayWeatherInsights.vue'
import TodayPrepTabs from '@/components/exercise/TodayPrepTabs.vue'
import WeatherRadar from '@/components/exercise/WeatherRadar.vue'
import SunTimeline from '@/components/exercise/SunTimeline.vue'
import SevereWeatherBanner from '@/components/exercise/SevereWeatherBanner.vue'
import { useConfigStore } from '@/stores/configStore'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()
const weather = ref(null)
const errorMessage = ref('')
// 전일 대비 기온 차이 (기록 없으면 null)
const tempDiffInfo = ref(null)
// 공유 버튼 복사 완료 표시
const shareCopied = ref(false)
// 기온/습도·강수확률 그래프 탭 전환
const trendTab = ref('temp')
const selectedDate = ref(typeof route.query.date === 'string' ? route.query.date : '')
// 시간별 예보 아코디언 펼침 여부
const hourlyExpanded = ref(true)
function selectDay(date) {
  if (date === selectedDate.value) {
    hourlyExpanded.value = !hourlyExpanded.value
    return
  }
  selectedDate.value = date
  hourlyExpanded.value = true
}
const city = computed(() => cityFromQuery(route.query))
const selectedDay = computed(() => weather.value?.daily.find((day) => day.date === selectedDate.value) ?? weather.value?.daily[0])
// 날씨 코드 기반 히어로 배경 테마 판단
const weatherThemeClass = computed(() => {
  const code = weather.value?.current.code
  const windGust = weather.value?.current.windGust ?? 0
  if (windGust >= 45) return 'weather-wind'
  if (code >= 200 && code <= 232) return 'weather-storm'
  if (code >= 600 && code <= 622) return 'weather-snow'
  if (code >= 701 && code <= 781) return 'weather-fog'
  if ((code >= 300 && code <= 321) || (code >= 500 && code <= 531)) return 'weather-rain'
  if (code === 801 || code === 802 || code === 803 || code === 804) return 'weather-cloud'
  return 'weather-clear'
})

watch(selectedDate, (date) => router.replace({ query: { ...route.query, date: date || undefined } }))

// 기온 추세 그래프용 SVG 좌표 계산
const trendChart = computed(() => {
  const days = weather.value?.daily ?? []
  if (days.length < 2) return null
  const allTemps = days.flatMap((day) => [day.max, day.min])
  const highest = Math.max(...allTemps)
  const lowest = Math.min(...allTemps)
  const range = highest - lowest || 1
  const width = 640
  const height = 190
  const padX = 34
  const padY = 34
  const stepX = (width - padX * 2) / (days.length - 1)
  // 섭씨 값 -> SVG y좌표 변환
  const toY = (temp) => height - padY - ((temp - lowest) / range) * (height - padY * 2)
  const maxPoints = days.map((day, index) => ({ x: padX + stepX * index, y: toY(day.max), day }))
  const minPoints = days.map((day, index) => ({ x: padX + stepX * index, y: toY(day.min), day }))
  return {
    width,
    height,
    maxPoints,
    minPoints,
    maxPolyline: maxPoints.map((p) => `${p.x},${p.y}`).join(' '),
    minPolyline: minPoints.map((p) => `${p.x},${p.y}`).join(' '),
  }
})

// 습도·강수확률 추세 그래프용 SVG 좌표 계산 (0~100 고정)
const humidityRainChart = computed(() => {
  const days = weather.value?.daily ?? []
  if (days.length < 2) return null
  const width = 640
  const height = 190
  const padX = 34
  const padY = 34
  const stepX = (width - padX * 2) / (days.length - 1)
  const toY = (percent) => height - padY - (percent / 100) * (height - padY * 2)
  const humidityPoints = days.map((day, index) => ({ x: padX + stepX * index, y: toY(day.humidity), day }))
  const rainPoints = days.map((day, index) => ({ x: padX + stepX * index, y: toY(day.rain), day }))
  return {
    width,
    height,
    humidityPoints,
    rainPoints,
    humidityPolyline: humidityPoints.map((p) => `${p.x},${p.y}`).join(' '),
    rainPolyline: rainPoints.map((p) => `${p.x},${p.y}`).join(' '),
  }
})

async function loadWeather() {
  errorMessage.value = ''
  weather.value = null
  tempDiffInfo.value = null
  if (!city.value) {
    errorMessage.value = '도시 정보가 올바르지 않습니다. 홈에서 지역을 다시 선택해 주세요.'
    return
  }
  try {
    weather.value = await fetchWeather(city.value)
    if (!selectedDate.value || !weather.value.daily.some((day) => day.date === selectedDate.value)) selectedDate.value = weather.value.daily[0].date
    // 최근 조회 도시 목록 갱신
    configStore.visitCity(weather.value.city)
    // 전일 대비 기온 차이 계산
    tempDiffInfo.value = configStore.recordTempAndGetDiff(weather.value.city.id, weather.value.daily[0].date, weather.value.current.temp)
  } catch (error) {
    console.error(error)
    errorMessage.value = '예보를 불러오지 못했습니다.'
  }
}

// 현재 페이지 URL 클립보드에 복사
async function shareCurrentView() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    shareCopied.value = true
    configStore.showToast('링크를 복사했어요.', 'success')
    setTimeout(() => (shareCopied.value = false), 1800)
  } catch (error) {
    console.error(error)
    configStore.showToast('링크 복사에 실패했습니다.', 'warning')
  }
}

onMounted(loadWeather)
</script>

<template>
  <main class="page-container narrow">
    <!-- 돌아가기·공유 버튼 -->
    <div class="page-top-row">
      <button class="text-button" @click="router.back()">← 돌아가기</button>
      <button v-if="weather" type="button" class="button share-button" @click="shareCurrentView">{{ shareCopied ? '✓ 복사됨' : '🔗 공유' }}</button>
    </div>
    <p v-if="errorMessage" class="message error">
      {{ errorMessage }}
      <button v-if="city" @click="loadWeather">다시 시도</button>
      <RouterLink v-else to="/">홈으로 이동</RouterLink>
    </p>
    <template v-else-if="weather">
      <header :class="['detail-hero', weatherThemeClass]">
        <!-- 날씨별 배경 애니메이션 + 아이콘 워터마크 -->
        <div class="weather-fx" aria-hidden="true">
          <span class="weather-fx-icon">{{ weatherCodeIcon(weather.current.code) }}</span>
        </div>
        <div>
          <p class="eyebrow">오늘의 날씨</p>
          <h1>{{ weather.city.name }}</h1>
          <p>{{ weather.city.country }} · {{ weather.city.admin }}</p>
        </div>
        <div class="current-big">
          <span>{{ weatherCodeIcon(weather.current.code) }}</span
          ><strong>{{ configStore.formatTemperature(weather.current.temp) }}</strong
          ><small>{{ weatherCodeText(weather.current.code) }}</small>
          <!-- 전일 대비 기온 변화 배지 -->
          <span v-if="tempDiffInfo" class="temp-diff-badge" :class="{ up: tempDiffInfo.diff > 0, down: tempDiffInfo.diff < 0 }">
            {{ tempDiffInfo.diff > 0 ? '▲' : tempDiffInfo.diff < 0 ? '▼' : '－' }} {{ Math.abs(tempDiffInfo.diff) }}℃
            {{ tempDiffInfo.isExactlyYesterday ? '어제보다' : '지난 확인보다' }}
          </span>
        </div>
      </header>
      <!-- 자체 판단 배너 + 기상청 공식 특보 -->
      <SevereWeatherBanner :daily="weather.daily" :city="weather.city" />
      <!-- 오늘 날씨 요약 + 준비/주의점 탭 -->
      <TodayWeatherInsights :current="weather.current" :today="weather.daily[0]" />
      <TodayPrepTabs :current="weather.current" :today="weather.daily[0]" />
      <!-- 일출·일몰 시각과 낮 시간 진행률 -->
      <SunTimeline :current="weather.current" :today="weather.daily[0]" />
      <section v-if="selectedDay" class="selected-day">
        <div>
          <span>{{ weatherCodeIcon(selectedDay.code) }}</span>
          <div>
            <p>{{ selectedDay.date }}</p>
            <h2>{{ weatherCodeText(selectedDay.code) }}</h2>
          </div>
        </div>
        <dl>
          <div>
            <dt>최고</dt>
            <dd>{{ configStore.formatTemperature(selectedDay.max) }}</dd>
          </div>
          <div>
            <dt>최저</dt>
            <dd>{{ configStore.formatTemperature(selectedDay.min) }}</dd>
          </div>
          <div>
            <dt>강수 확률</dt>
            <dd>{{ selectedDay.rain }}%</dd>
          </div>
        </dl>
      </section>
      <input v-model="selectedDate" class="date-picker" type="date" :min="weather.daily[0].date" :max="weather.daily.at(-1).date" />
      <!-- 일자별 카드 + 시간별 예보 아코디언 -->
      <section class="forecast-box">
        <div class="forecast-row">
          <button
            v-for="day in weather.daily"
            :key="day.date"
            :class="{ active: day.date === selectedDay.date && hourlyExpanded }"
            :aria-expanded="day.date === selectedDay.date && hourlyExpanded"
            @click="selectDay(day.date)"
          >
            <small>{{ day.date.slice(5) }}</small
            ><span>{{ weatherCodeIcon(day.code) }}</span
            ><strong>{{ configStore.formatTemperature(day.max) }}</strong
            ><small>{{ configStore.formatTemperature(day.min) }} · 비 {{ day.rain }}%</small>
          </button>
        </div>

        <!-- 시간별 예보 아코디언 (grid-template-rows 트릭) -->
        <div v-if="selectedDay?.hourly?.length" class="hourly-subsection">
          <div class="section-heading">
            <div>
              <p class="eyebrow">{{ selectedDay.date }}</p>
              <h2>시간별 예보</h2>
            </div>
            <button type="button" class="hourly-toggle-button" :aria-expanded="hourlyExpanded" @click="hourlyExpanded = !hourlyExpanded">
              {{ hourlyExpanded ? '접기 ▲' : '펼치기 ▼' }}
            </button>
          </div>
          <div class="hourly-collapse" :class="{ open: hourlyExpanded }">
            <div class="hourly-collapse-inner">
              <div class="hourly-row">
                <article v-for="slot in selectedDay.hourly" :key="slot.time" class="hourly-item">
                  <small>{{ slot.time }}</small>
                  <span>{{ weatherCodeIcon(slot.code) }}</span>
                  <strong>{{ configStore.formatTemperature(slot.temp) }}</strong>
                  <small class="hourly-rain">☔ {{ slot.rain }}%</small>
                </article>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 기온 / 습도·강수확률 추세 그래프 탭 -->
      <section v-if="trendChart || humidityRainChart" class="temp-trend-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">추세 보기</p>
            <h2>{{ trendTab === 'temp' ? '기온 변화 그래프' : '습도 · 강수확률 추이' }}</h2>
          </div>
          <span>최근 {{ weather.daily.length }}일 {{ trendTab === 'temp' ? '최고·최저 기온' : '습도·강수확률' }} 흐름입니다.</span>
        </div>
        <div class="trend-tabs" role="tablist" aria-label="추세 그래프 종류">
          <button type="button" role="tab" :aria-selected="trendTab === 'temp'" :class="{ active: trendTab === 'temp' }" @click="trendTab = 'temp'">기온</button>
          <button type="button" role="tab" :aria-selected="trendTab === 'humidity'" :class="{ active: trendTab === 'humidity' }" @click="trendTab = 'humidity'">습도 · 강수확률</button>
        </div>
        <svg
          v-if="trendTab === 'temp' && trendChart"
          :viewBox="`0 0 ${trendChart.width} ${trendChart.height}`"
          class="temp-trend-svg"
          role="img"
          :aria-label="`${weather.city.name}의 ${weather.daily.length}일 최고·최저 기온 변화 그래프`"
        >
          <polyline :points="trendChart.maxPolyline" class="trend-line trend-line-max" />
          <polyline :points="trendChart.minPolyline" class="trend-line trend-line-min" />
          <g v-for="point in trendChart.maxPoints" :key="`max-${point.day.date}`">
            <circle :cx="point.x" :cy="point.y" r="4" class="trend-dot trend-dot-max" />
            <text :x="point.x" :y="point.y - 10" class="trend-value trend-value-max">{{ configStore.formatTemperature(point.day.max) }}</text>
            <text :x="point.x" :y="trendChart.height - 6" class="trend-date">{{ point.day.date.slice(5) }}</text>
          </g>
          <g v-for="point in trendChart.minPoints" :key="`min-${point.day.date}`">
            <circle :cx="point.x" :cy="point.y" r="4" class="trend-dot trend-dot-min" />
            <text :x="point.x" :y="point.y + 18" class="trend-value trend-value-min">{{ configStore.formatTemperature(point.day.min) }}</text>
          </g>
        </svg>
        <svg
          v-else-if="humidityRainChart"
          :viewBox="`0 0 ${humidityRainChart.width} ${humidityRainChart.height}`"
          class="temp-trend-svg"
          role="img"
          :aria-label="`${weather.city.name}의 ${weather.daily.length}일 습도·강수확률 변화 그래프`"
        >
          <polyline :points="humidityRainChart.humidityPolyline" class="trend-line trend-line-humidity" />
          <polyline :points="humidityRainChart.rainPolyline" class="trend-line trend-line-rain" />
          <g v-for="point in humidityRainChart.humidityPoints" :key="`humidity-${point.day.date}`">
            <circle :cx="point.x" :cy="point.y" r="4" class="trend-dot trend-dot-humidity" />
            <text :x="point.x" :y="point.y - 10" class="trend-value trend-value-humidity">{{ point.day.humidity }}%</text>
            <text :x="point.x" :y="humidityRainChart.height - 6" class="trend-date">{{ point.day.date.slice(5) }}</text>
          </g>
          <g v-for="point in humidityRainChart.rainPoints" :key="`rain-${point.day.date}`">
            <circle :cx="point.x" :cy="point.y" r="4" class="trend-dot trend-dot-rain" />
            <text :x="point.x" :y="point.y + 18" class="trend-value trend-value-rain">{{ point.day.rain }}%</text>
          </g>
        </svg>
        <div class="trend-legend">
          <template v-if="trendTab === 'temp'">
            <span class="trend-legend-max">● 최고기온</span>
            <span class="trend-legend-min">● 최저기온</span>
          </template>
          <template v-else>
            <span class="trend-legend-humidity">● 평균 습도</span>
            <span class="trend-legend-rain">● 강수확률</span>
          </template>
        </div>
      </section>

      <WeatherRadar :latitude="weather.city.latitude" :longitude="weather.city.longitude" :city-name="weather.city.name" />
    </template>
    <div v-else class="loading">예보를 불러오는 중입니다…</div>
  </main>
</template>
