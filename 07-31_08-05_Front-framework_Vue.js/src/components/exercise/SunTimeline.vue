<script setup>
import { computed } from 'vue'
import { sunPositionInfo } from '@/services/openWeatherApi'

// 낮 경과율을 막대 위 해 아이콘 위치로 표시
const props = defineProps({ current: { type: Object, required: true }, today: { type: Object, required: true } })
const info = computed(() => sunPositionInfo(props.current, props.today))
</script>

<template>
  <section class="sun-timeline">
    <div class="section-heading">
      <div>
        <p class="eyebrow">해가 떠 있는 시간</p>
        <h2>일출 · 일몰</h2>
      </div>
      <span v-if="info.remainingLabel">{{ info.remainingLabel }}</span>
    </div>
    <div class="sun-track">
      <span class="sun-track-icon" :style="{ left: `${info.percent}%` }" aria-hidden="true">{{ info.isDaytime ? '☀️' : '🌙' }}</span>
      <div class="sun-track-bar"><div class="sun-track-fill" :style="{ width: `${info.percent}%` }" /></div>
      <!-- 일출(0%)~일몰(100%) 라벨 -->
      <div class="sun-track-labels">
        <span class="sun-track-label sun-track-label-start">🌅 {{ info.sunriseLabel }}</span>
        <span class="sun-track-label sun-track-label-end">🌇 {{ info.sunsetLabel }}</span>
      </div>
    </div>
  </section>
</template>
