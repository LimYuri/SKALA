<script setup>
import { computed, ref } from 'vue'
import { airQualityText, clothingRecommendation, foodRecommendation } from '@/services/openWeatherApi'
import { useHoverIndex } from '@/composables/useHover'

// 알림 / 옷차림·음식 탭
const props = defineProps({ current: { type: Object, required: true }, today: { type: Object, required: true } })
const prepTab = ref('advisory') // 'advisory' | 'clothing'
const advisoryHover = useHoverIndex()

// 수치 기반 오늘의 준비/주의사항 목록
const advisories = computed(() => {
  const items = []
  if (props.today.rain >= 40 || props.today.precipitation >= 1)
    items.push({ icon: '☂️', title: '우산 챙기기', text: `강수 확률 ${props.today.rain}%, 예상 강수량 ${props.today.precipitation}mm입니다.` })
  if (props.today.windGustMax >= 40) items.push({ icon: '💨', title: '강풍 주의', text: `최대 순간풍속이 ${props.today.windGustMax}km/h까지 예상됩니다. 가벼운 물건과 시설물에 주의하세요.` })
  if (props.current.visibility < 5) items.push({ icon: '🚗', title: '시야 확보', text: `가시거리가 ${props.current.visibility}km입니다. 운전할 때 감속하고 안전거리를 확보하세요.` })
  if (props.current.feels >= 33) items.push({ icon: '🥤', title: '온열질환 주의', text: '체감온도가 높습니다. 물을 자주 마시고 한낮의 장시간 야외활동을 줄이세요.' })
  if (props.current.feels <= 0) items.push({ icon: '🧣', title: '보온 준비', text: '체감온도가 영하권입니다. 장갑과 목도리 등 방한용품을 챙기세요.' })
  if (props.current.code >= 200 && props.current.code <= 232) items.push({ icon: '⚡', title: '낙뢰 주의', text: '천둥·번개가 예상됩니다. 탁 트인 야외와 높은 구조물을 피하세요.' })
  if (props.current.air?.aqi >= 4)
    items.push({
      icon: '😷',
      title: '미세먼지 주의',
      text: `대기질이 ${airQualityText(props.current.air.aqi)} 수준입니다(PM2.5 ${props.current.air.pm2_5}㎍/㎥). 마스크를 착용하고 장시간 야외활동은 줄이세요.`,
    })
  if (!items.length) items.push({ icon: '✅', title: '큰 기상 위험 없음', text: '현재 수치상 특별한 위험 신호는 없습니다. 외출 전 최신 예보를 한 번 더 확인하세요.' })
  return items
})

const clothing = computed(() => clothingRecommendation(props.current.feels))
const food = computed(() => foodRecommendation(props.current.feels, props.today.rain, props.current.code))
</script>

<template>
  <section class="today-prep-section" aria-labelledby="today-prep-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">{{ prepTab === 'advisory' ? '오늘 챙길 것' : `체감온도 ${Math.round(current.feels)}℃ 기준` }}</p>
        <h2 id="today-prep-title">{{ prepTab === 'advisory' ? '오늘의 알림' : '오늘 뭐 입고, 뭐 먹지?' }}</h2>
      </div>
    </div>
    <div class="trend-tabs" role="tablist" aria-label="오늘의 준비 종류">
      <button type="button" role="tab" :aria-selected="prepTab === 'advisory'" :class="{ active: prepTab === 'advisory' }" @click="prepTab = 'advisory'">알림</button>
      <button type="button" role="tab" :aria-selected="prepTab === 'clothing'" :class="{ active: prepTab === 'clothing' }" @click="prepTab = 'clothing'">옷차림 · 음식</button>
    </div>
    <div v-if="prepTab === 'advisory'" class="advisory-grid">
      <article
        v-for="(item, index) in advisories"
        :key="item.title"
        :class="{ 'is-hovered': advisoryHover.isHovered(index) }"
        @mouseenter="advisoryHover.onEnter(index)"
        @mouseleave="advisoryHover.onLeave"
      >
        <span>{{ item.icon }}</span>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.text }}</p>
        </div>
      </article>
    </div>
    <div v-else class="tips-grid">
      <article class="tip-card">
        <span class="tip-icon" aria-hidden="true">{{ clothing.icon }}</span>
        <div>
          <p class="tip-label">오늘의 옷차림</p>
          <strong>{{ clothing.title }}</strong>
          <p class="tip-desc">{{ clothing.desc }}</p>
        </div>
      </article>
      <article class="tip-card">
        <span class="tip-icon" aria-hidden="true">{{ food.icon }}</span>
        <div>
          <p class="tip-label">오늘의 추천 메뉴</p>
          <strong>{{ food.title }}</strong>
          <p class="tip-desc">{{ food.desc }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
