<script setup>
import { useConfigStore } from '@/stores/configStore'
const configStore = useConfigStore()
</script>

<template>
  <div class="unit-toggle">
    <span>{{ configStore.unitSymbol }}</span>
    <!-- 섭씨/화씨 전환 스위치 -->
    <a-switch :checked="configStore.unit === 'fahrenheit'" aria-label="섭씨 화씨 전환" checked-children="℉" un-checked-children="℃" @change="configStore.toggleUnit" />
  </div>
</template>

<style scoped>
.unit-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  /* topbar 오른쪽 끝으로 정렬 */
  margin-left: auto;
  font-weight: 800;
}
</style>
