<script setup>
import { computed, ref, watch } from 'vue'
import { severeWeatherWarnings } from '@/services/openWeatherApi'
import { fetchWeatherAlerts } from '@/services/weatherAlertApi'

// 자체 판단 주의보/경보(warnings) + 기상청 공식 특보(officialAlerts)
const props = defineProps({ daily: { type: Array, required: true }, city: { type: Object, default: null } })
const warnings = computed(() => severeWeatherWarnings(props.daily))

const officialAlerts = ref([])
// 키 없거나 실패해도 조용히 빈 배열 처리
watch(
  () => props.city,
  async (city) => {
    officialAlerts.value = []
    if (!city) return
    try {
      officialAlerts.value = await fetchWeatherAlerts(city)
    } catch (error) {
      console.warn('기상특보 조회에 실패했습니다.', error)
    }
  },
  { immediate: true },
)
</script>

<template>
  <div v-if="officialAlerts.length || warnings.length" class="severe-wrapper">
    <!-- 기상청 공식 특보 -->
    <section v-if="officialAlerts.length" class="severe-banner official" aria-live="polite">
      <p class="severe-official-label">기상청 공식 특보</p>
      <article v-for="item in officialAlerts" :key="item.title + item.announcedAt" class="severe-item severe-warning">
        <span aria-hidden="true">{{ item.icon }}</span>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.area }} · {{ item.announcedAt || '발표 시각 정보 없음' }}</p>
        </div>
      </article>
    </section>
    <section v-if="warnings.length" class="severe-banner" aria-live="polite">
      <article v-for="item in warnings" :key="item.title" :class="['severe-item', `severe-${item.level}`]">
        <span aria-hidden="true">{{ item.icon }}</span>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.text }}</p>
        </div>
      </article>
    </section>
  </div>
</template>
