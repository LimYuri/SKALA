<template>
  <span class="gearhub-logo" :class="{ 'symbol-only': !showWordmark }" aria-hidden="true">
    <span class="gearhub-mark">
      <img src="@/assets/brand/use-monogram.png" alt="" />
    </span>
    <span v-if="showWordmark" class="gearhub-wordmark">
      <strong><em>U</em>niversal <em>S</em>torag<em>E</em></strong>
    </span>
  </span>
</template>

<script setup>
defineProps({
  showWordmark: { type: Boolean, default: true }
})
</script>

<style scoped>
.gearhub-logo {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--color-primary, #2563eb);
  line-height: 1;
}
.gearhub-mark {
  width: 39px;
  height: 39px;
  flex: 0 0 39px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, .82);
  border: 1px solid color-mix(in srgb, var(--color-primary, #2563eb) 22%, transparent);
  border-radius: 12px;
  box-shadow: 0 7px 20px rgba(40, 70, 92, .08);
}
.gearhub-mark img {
  width: 29px;
  height: 29px;
  display: block;
  object-fit: contain;
}
.gearhub-wordmark {
  display: flex;
  flex-direction: column;
}
.gearhub-wordmark strong {
  color: var(--color-navy, #102a56);
  font-family: var(--font-display, 'Plus Jakarta Sans', 'Noto Sans KR', sans-serif);
  font-size: 15px;
  font-weight: 850;
  letter-spacing: -.02em;
}
.gearhub-wordmark em { color: var(--color-primary, #2563eb); font-style: normal; }
.symbol-only { gap: 0; }

@media (max-width: 390px) {
  .gearhub-wordmark { display: none; }
}
</style>
