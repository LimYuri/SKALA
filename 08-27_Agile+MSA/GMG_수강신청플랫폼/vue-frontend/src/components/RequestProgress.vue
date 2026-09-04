<template>
  <div v-if="terminalFailure" class="terminal-state">
    <span aria-hidden="true"><AppIcon name="alert" :size="17" /></span>
    <strong>{{ statusMeta(status).label }}</strong>
    <small>{{ statusMeta(status).next }}</small>
  </div>
  <ol v-else class="request-progress" :aria-label="`${type === 'PURCHASE' ? '도입' : '대여'} 진행 단계`">
    <li
      v-for="(step, index) in steps"
      :key="step.status"
      :class="{
        complete: index < activeIndex || (terminalComplete && index === activeIndex),
        active: !terminalComplete && index === activeIndex
      }"
      :aria-current="!terminalComplete && index === activeIndex ? 'step' : undefined"
    >
      <span class="step-marker">
        <AppIcon v-if="index < activeIndex || (terminalComplete && index === activeIndex)" name="check" :size="13" />
        <template v-else>{{ index + 1 }}</template>
      </span>
      <small>{{ step.label }}</small>
    </li>
  </ol>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { requestProgressIndex, requestSteps, statusMeta } from '@/utils/requestStatus.js'

const props = defineProps({
  type: { type: String, default: 'LOAN' },
  status: { type: String, required: true }
})

const steps = computed(() => requestSteps(props.type))
const activeIndex = computed(() => requestProgressIndex(props.type, props.status))
const terminalFailure = computed(() => ['REJECTED', 'CANCELLED'].includes(props.status))
const terminalComplete = computed(() => ['RETURNED', 'RECEIVED'].includes(props.status))
</script>

<style scoped>
.request-progress {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  padding: 0;
  list-style: none;
}
.request-progress li {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  color: var(--color-text-muted);
  text-align: center;
}
.request-progress li:not(:last-child)::after {
  content: '';
  position: absolute;
  z-index: 0;
  top: 11px;
  left: calc(50% + 12px);
  width: calc(100% - 24px);
  height: 2px;
  background: var(--color-border);
}
.request-progress li.complete:not(:last-child)::after {
  background: #79a7e8;
}
.step-marker {
  position: relative;
  z-index: 1;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  color: var(--color-text-muted);
  background: #fff;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  font-size: 9px;
  font-weight: 800;
}
.complete .step-marker {
  color: #fff;
  background: var(--color-success);
  border-color: var(--color-success);
}
.active .step-marker {
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}
.request-progress small {
  font-size: 9px;
  font-weight: 650;
}
.active small {
  color: var(--color-primary);
  font-weight: 800;
}
.terminal-state {
  display: grid;
  grid-template-columns: 30px 1fr;
  column-gap: 9px;
  padding: 10px 12px;
  color: var(--color-danger);
  background: var(--color-danger-light);
  border-radius: 10px;
}
.terminal-state > span {
  grid-row: 1 / 3;
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-danger);
  border-radius: 9px;
  font-weight: 800;
}
.terminal-state strong { font-size: 11px; }
.terminal-state small { font-size: 9px; }
</style>
