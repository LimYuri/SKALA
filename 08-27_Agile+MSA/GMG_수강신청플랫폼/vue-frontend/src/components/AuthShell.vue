<template>
  <main class="auth-page">
    <div class="auth-atmosphere" aria-hidden="true"></div>

    <section class="auth-layout">
      <aside class="auth-brand-panel" aria-label="Universal StoragE 소개">
        <router-link to="/" class="auth-brand" aria-label="Universal StoragE 홈">
          <GearHubLogo class="auth-brand-logo" aria-hidden="true" />
        </router-link>
      </aside>

      <div class="auth-main-panel">
        <router-link :to="closeTo" class="auth-close" :aria-label="closeLabel">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m6 6 12 12M18 6 6 18" />
          </svg>
        </router-link>

        <div class="auth-content fade-in-up">
          <slot></slot>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import GearHubLogo from '@/components/GearHubLogo.vue'

defineProps({
  closeTo: {
    type: [String, Object],
    default: '/'
  },
  closeLabel: {
    type: String,
    default: '닫고 홈으로 이동'
  }
})

</script>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 32px;
  background: #f3f7fd;
}

.auth-atmosphere {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 12% 16%, rgba(37, 99, 235, .12), transparent 34%),
    radial-gradient(circle at 90% 82%, rgba(59, 130, 246, .09), transparent 30%);
}

.auth-layout {
  position: relative;
  z-index: 1;
  width: min(1040px, 100%);
  min-height: 660px;
  display: grid;
  grid-template-columns: minmax(340px, .92fr) minmax(430px, 1.08fr);
  overflow: hidden;
  background: rgba(255, 255, 255, .84);
  border: 1px solid rgba(194, 211, 235, .78);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
}

.auth-brand-panel {
  padding: 44px 46px 36px;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(145deg, rgba(229, 238, 252, .96), rgba(239, 245, 255, .9)),
    #eef4fd;
  border-right: 1px solid rgba(194, 211, 235, .7);
}

.auth-brand {
  width: fit-content;
  display: inline-flex;
  align-items: center;
  gap: 11px;
  border-radius: var(--radius-sm);
}

.auth-brand-copy {
  margin-block: auto;
  padding-block: 56px;
}

.auth-brand-heading {
  color: var(--color-navy);
  font-size: clamp(30px, 3.4vw, 40px);
  line-height: 1.27;
  letter-spacing: -.045em;
}

.auth-brand-description {
  max-width: 340px;
  margin-top: 17px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.75;
}

.auth-feature-list {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  list-style: none;
}

.auth-feature-list li {
  display: flex;
  align-items: center;
  gap: 11px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 650;
}

.auth-feature-list li span {
  position: relative;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  border: 1px solid rgba(37, 99, 235, .28);
  border-radius: 50%;
  background: rgba(255, 255, 255, .6);
}

.auth-feature-list li span::after {
  content: '';
  position: absolute;
  inset: 5px;
  border-radius: 50%;
  background: var(--color-primary);
}

.auth-main-panel {
  position: relative;
  min-width: 0;
  display: grid;
  place-items: center;
  padding: 68px 58px 52px;
  background: rgba(255, 255, 255, .88);
}

.auth-close {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, .65);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  transition: var(--transition);
}

.auth-close:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  transform: translateY(-1px);
}

.auth-close:active {
  transform: translateY(0) scale(.97);
}

.auth-close svg {
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
}

.auth-content {
  width: min(100%, 410px);
}

@media (max-width: 820px) {
  .auth-page {
    place-items: start center;
    overflow: visible;
    padding: 20px;
  }

  .auth-layout {
    min-height: auto;
    grid-template-columns: 1fr;
  }

  .auth-brand-panel {
    padding: 24px 28px;
    border-right: 0;
    border-bottom: 1px solid rgba(194, 211, 235, .7);
  }

  .auth-brand-copy {
    padding: 30px 0 0;
  }

  .auth-brand-heading {
    font-size: clamp(25px, 7vw, 32px);
  }

  .auth-brand-description {
    margin-top: 10px;
  }

  .auth-feature-list {
    display: none;
  }

  .auth-main-panel {
    place-items: start center;
    padding: 64px 36px 42px;
  }

  .auth-close {
    top: 14px;
    right: 16px;
  }
}

@media (max-width: 520px) {
  .auth-page {
    padding: 0;
    background: var(--color-bg-primary);
  }

  .auth-layout {
    width: 100%;
    min-height: 100vh;
    border: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .auth-brand-panel {
    padding: 20px 22px;
  }

  .auth-brand-copy {
    padding-top: 24px;
  }

  .auth-main-panel {
    padding: 62px 22px 36px;
  }
}
</style>
