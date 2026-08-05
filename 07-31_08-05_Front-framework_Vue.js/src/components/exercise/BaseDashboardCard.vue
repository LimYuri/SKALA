<script setup>
// 카드 바깥 틀 재사용, 내용은 슬롯으로 채움
defineProps({ eyebrow: { type: String, default: '' }, title: { type: String, default: '' } })
</script>

<template>
  <section class="dashboard-card">
    <p v-if="eyebrow || $slots.eyebrow" class="eyebrow">
      <slot name="eyebrow">{{ eyebrow }}</slot>
    </p>
    <h1 v-if="title || $slots.title">
      <slot name="title">{{ title }}</slot>
    </h1>
    <slot />
  </section>
</template>
