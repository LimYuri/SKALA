<script setup>
// 전역 토스트 알림, 상태는 configStore에서 관리
import { useConfigStore } from '@/stores/configStore'
const configStore = useConfigStore()
</script>

<template>
  <!-- Teleport로 body 최상위에 렌더링 (z-index 걱정 없이 항상 위에 표시) -->
  <Teleport to="body">
    <Transition name="toast-fade">
      <p v-if="configStore.toast" class="toast" :class="configStore.toast.type" role="status">{{ configStore.toast.text }}</p>
    </Transition>
  </Teleport>
</template>
