<script setup>
// 라이트/다크 모드 토글 (a-switch + Pinia)
import { useConfigStore } from '@/stores/configStore'
const configStore = useConfigStore()
</script>

<template>
  <div class="theme-toggle">
    <span aria-hidden="true">{{ configStore.theme === 'dark' ? '🌙' : '☀️' }}</span>
    <a-switch :checked="configStore.theme === 'dark'" aria-label="라이트 다크 모드 전환" checked-children="다크" un-checked-children="라이트" @change="configStore.toggleTheme" />
  </div>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-weight: 800;
}
</style>
