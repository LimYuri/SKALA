<script setup>
// 체감온도 기반 옷차림·음식 추천 카드
import { computed } from 'vue'
import { clothingRecommendation, foodRecommendation } from '@/services/openWeatherApi'

const props = defineProps({
  feels: { type: Number, required: true },
  rain: { type: Number, default: 0 },
  code: { type: Number, required: true },
})

const clothing = computed(() => clothingRecommendation(props.feels))
const food = computed(() => foodRecommendation(props.feels, props.rain, props.code))
</script>

<template>
  <section class="tips-section" aria-labelledby="tips-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">체감온도 {{ Math.round(feels) }}℃ 기준</p>
        <h2 id="tips-title">오늘 뭐 입고, 뭐 먹지?</h2>
      </div>
    </div>
    <div class="tips-grid">
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
