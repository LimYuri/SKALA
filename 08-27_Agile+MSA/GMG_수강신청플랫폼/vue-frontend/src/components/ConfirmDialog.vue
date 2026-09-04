<template>
  <Teleport to="body">
    <transition name="dialog-fade">
      <div v-if="open" class="dialog-backdrop" @click.self="$emit('cancel')">
        <section
          ref="dialog"
          class="confirm-dialog"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          :aria-describedby="descriptionId"
        >
          <span :class="['dialog-icon', `tone-${tone}`]" aria-hidden="true"><AppIcon :name="icon" :size="21" /></span>
          <div>
            <h2 :id="titleId">{{ title }}</h2>
            <p :id="descriptionId">{{ description }}</p>
          </div>
          <div class="dialog-actions">
            <button class="btn btn-ghost" type="button" @click="$emit('cancel')">취소</button>
            <button ref="confirmButton" :class="['btn', tone === 'danger' ? 'btn-danger' : 'btn-primary']" type="button" @click="$emit('confirm')">
              {{ confirmLabel }}
            </button>
          </div>
        </section>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/AppIcon.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  description: { type: String, required: true },
  confirmLabel: { type: String, default: '확인' },
  tone: { type: String, default: 'primary' }
})

const emit = defineEmits(['cancel', 'confirm'])
const uid = Math.random().toString(36).slice(2, 9)
const titleId = `confirm-title-${uid}`
const descriptionId = `confirm-description-${uid}`
const icon = computed(() => props.tone === 'danger' ? 'alert' : 'check')
const dialog = ref(null)
const confirmButton = ref(null)
let previouslyFocused = null
let previousOverflow = ''

function onKeydown(event) {
  if (!props.open) return
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('cancel')
    return
  }
  if (event.key !== 'Tab') return
  const focusable = [...(dialog.value?.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])') || [])]
  if (!focusable.length) return
  const first = focusable[0]
  const last = focusable.at(-1)
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(() => props.open, async open => {
  if (open) {
    previouslyFocused = document.activeElement
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    await nextTick()
    confirmButton.value?.focus()
    return
  }
  document.body.style.overflow = previousOverflow
  previouslyFocused?.focus?.()
  previouslyFocused = null
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = previousOverflow
})
</script>

<style scoped>
.dialog-backdrop {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(7, 24, 36, .55);
  backdrop-filter: blur(3px);
}
.confirm-dialog {
  width: min(100%, 430px);
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 14px;
  padding: 24px;
  background: #fff;
  border-radius: 18px;
  box-shadow: var(--shadow-lg);
}
.dialog-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  font-size: 18px;
  font-weight: 800;
}
.dialog-icon.tone-primary { color: var(--color-primary); background: var(--color-primary-light); }
.dialog-icon.tone-danger { color: var(--color-danger); background: var(--color-danger-light); }
.confirm-dialog h2 {
  color: var(--color-navy);
  font-size: 18px;
  line-height: 1.35;
}
.confirm-dialog p {
  margin-top: 7px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.65;
}
.dialog-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 7px;
}
.dialog-fade-enter-active,
.dialog-fade-leave-active { transition: opacity .18s ease; }
.dialog-fade-enter-from,
.dialog-fade-leave-to { opacity: 0; }
</style>
