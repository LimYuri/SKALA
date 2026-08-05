<script setup>
import { computed } from 'vue'
import { airQualityText, weatherCodeText, windDirectionText } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'
import { useHoverIndex } from '@/composables/useHover'

const props = defineProps({ current: { type: Object, required: true }, today: { type: Object, required: true } })
const configStore = useConfigStore()
// 상세 지표 카드 호버 인덱스
const detailHover = useHoverIndex()

const summary = computed(() => {
  const temperature = `현재 ${configStore.formatTemperature(props.current.temp)}, 체감 ${configStore.formatTemperature(props.current.feels)}`
  const sky = weatherCodeText(props.current.code)
  const wind = `${windDirectionText(props.current.windDirection)}풍 ${props.current.wind}km/h`
  const rain = `오늘 강수 확률 ${props.today.rain}%`
  return `${sky}이며 ${temperature}입니다. ${wind}, ${rain}로 예상됩니다.`
})

const details = computed(() => [
  { label: '체감온도', value: configStore.formatTemperature(props.current.feels), note: `실제 ${configStore.formatTemperature(props.current.temp)}` },
  { label: '습도', value: `${props.current.humidity}%`, note: props.current.humidity >= 70 ? '다소 습함' : '보통 수준' },
  { label: '바람', value: `${props.current.wind} km/h`, note: `${windDirectionText(props.current.windDirection)}풍 · 돌풍 ${props.current.windGust} km/h` },
  { label: '가시거리', value: `${props.current.visibility} km`, note: props.current.visibility < 5 ? '시야 주의' : '시야 양호' },
  { label: '구름량', value: `${props.current.cloudCover}%`, note: weatherCodeText(props.current.code) },
  { label: '강수량', value: `${props.current.precipitation} mm`, note: `오늘 누적 ${props.today.precipitation} mm` },
  { label: '미세먼지', value: props.current.air?.aqi ? `PM2.5 ${props.current.air.pm2_5}㎍/㎥` : '정보 없음', note: airQualityText(props.current.air?.aqi) },
])
</script>

<template>
  <section class="today-insights" aria-labelledby="today-summary-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">오늘 한눈에 보기</p>
        <h2 id="today-summary-title">오늘 날씨 요약</h2>
      </div>
      <span>관측 {{ current.observedAt.slice(11) }}</span>
    </div>
    <p class="weather-summary">{{ summary }}</p>
    <div class="detail-metrics">
      <article v-for="(item, index) in details" :key="item.label" :class="{ 'is-hovered': detailHover.isHovered(index) }" @mouseenter="detailHover.onEnter(index)" @mouseleave="detailHover.onLeave">
        <small>{{ item.label }}</small
        ><strong>{{ item.value }}</strong
        ><span>{{ item.note }}</span>
      </article>
    </div>
  </section>
</template>
