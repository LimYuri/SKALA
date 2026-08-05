<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { cityToQuery, comfortScore, weatherCodeIcon, weatherCodeText } from '@/services/openWeatherApi'
import { useConfigStore } from '@/stores/configStore'
import { useHoverFlag } from '@/composables/useHover'

const props = defineProps({ weather: { type: Object, required: true }, selected: { type: Boolean, default: false } })
const emit = defineEmits(['toggle-select', 'remove'])
const detailQuery = computed(() => cityToQuery(props.weather.city))
const configStore = useConfigStore()
// 오늘 쾌적지수 계산
const comfort = computed(() => comfortScore(props.weather))
// 카드 호버 강조 효과
const { isHovered, onEnter, onLeave } = useHoverFlag()
</script>

<template>
  <article :class="['weather-card', { selected, 'is-hovered': isHovered }]" @mouseenter="onEnter" @mouseleave="onLeave">
    <!-- 목록에서 도시 제거 -->
    <button class="remove-card" type="button" :aria-label="`${weather.city.name} 목록에서 제거`" title="목록에서 제거" @click="emit('remove', weather.city.id)">✕</button>
    <div class="card-title">
      <span>{{ weatherCodeIcon(weather.current.code) }}</span>
      <div>
        <h3>{{ weather.city.name }}</h3>
        <p>{{ weather.city.country }} {{ weather.city.admin }}</p>
      </div>
      <a-tag>{{ weatherCodeText(weather.current.code) }}</a-tag>
    </div>
    <strong class="temperature">{{ configStore.formatTemperature(weather.current.temp) }}</strong>
    <p>{{ weatherCodeText(weather.current.code) }} · 체감 {{ configStore.formatTemperature(weather.current.feels) }}</p>
    <!-- 점수 구간별 쾌적지수 배지 색상 변경 -->
    <p class="comfort-score" :class="`score-${comfort.level}`">
      <span aria-hidden="true">🌡️</span> 오늘 쾌적지수 <strong>{{ comfort.score }}점</strong> · {{ comfort.label }}
    </p>
    <dl>
      <div>
        <dt>습도</dt>
        <dd>{{ weather.current.humidity }}%</dd>
      </div>
      <div>
        <dt>풍속</dt>
        <dd>{{ weather.current.wind }} km/h</dd>
      </div>
    </dl>
    <div class="card-actions">
      <!-- 즐겨찾기 버튼은 .favorite 클래스로 금색 강조 -->
      <a-button :type="selected ? 'primary' : 'default'" @click="emit('toggle-select', weather.city.id)">{{ selected ? '✓ 비교 선택됨' : '+ 비교 선택' }}</a-button>
      <a-button :class="{ favorite: configStore.isFavorite(weather.city.id) }" @click="configStore.toggleFavorite(weather.city.id)">{{
        configStore.isFavorite(weather.city.id) ? '★ 즐겨찾기' : '☆ 즐겨찾기'
      }}</a-button>
      <RouterLink class="button primary" :to="{ name: 'weather-detail', params: { cityId: weather.city.id }, query: detailQuery }">상세보기</RouterLink>
    </div>
  </article>
</template>
