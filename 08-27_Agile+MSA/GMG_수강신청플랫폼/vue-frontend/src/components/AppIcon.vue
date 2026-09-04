<template>
  <svg
    class="app-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :width="size"
    :height="size"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    focusable="false"
  >
    <title v-if="label">{{ label }}</title>

    <template v-if="name === 'campus'">
      <path d="m3 10 9-6 9 6" />
      <path d="M5 10h14M6 20h12M7 10v10m5-10v10m5-10v10" />
    </template>
    <template v-else-if="name === 'grid'">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </template>
    <template v-else-if="name === 'device'">
      <rect x="7" y="2" width="10" height="20" rx="2.5" />
      <path d="M10 18h4" />
    </template>
    <template v-else-if="name === 'computer'">
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M8 21h8m-4-4v4" />
    </template>
    <template v-else-if="name === 'cloud'">
      <path d="M17.5 19H7a5 5 0 0 1-.7-9.95A7 7 0 0 1 19.7 11.5 3.8 3.8 0 0 1 17.5 19Z" />
    </template>
    <template v-else-if="name === 'circuit'">
      <circle cx="12" cy="12" r="2.5" />
      <circle cx="5" cy="5" r="1.5" />
      <circle cx="19" cy="5" r="1.5" />
      <circle cx="5" cy="19" r="1.5" />
      <circle cx="19" cy="19" r="1.5" />
      <path d="m10.2 10.2-4-4m7.6 4 4-4m-7.6 7.6-4 4m7.6-4 4 4" />
    </template>
    <template v-else-if="name === 'tools'">
      <path d="m14.5 6.5 3-3 3 3-3 3M13 8l3 3" />
      <path d="m10.5 13.5-6 6a1.4 1.4 0 0 1-2-2l6-6" />
      <path d="M4 4a4 4 0 0 0 5 5l6 6a3.5 3.5 0 0 0 5 5l-8-8a4 4 0 0 0-5-5Z" />
    </template>
    <template v-else-if="name === 'camera'">
      <path d="M14.5 5 16 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3l1.5-2h5Z" />
      <circle cx="12" cy="13" r="4" />
    </template>
    <template v-else-if="name === 'presentation'">
      <path d="M4 3h16v13H4zM2 3h20M12 16v5m-4 0 4-5 4 5" />
      <path d="m8 12 3-3 2 2 3-4" />
    </template>
    <template v-else-if="name === 'accessory'">
      <path d="M7 3v5m4-5v5M5 8h8v2a4 4 0 0 1-4 4v3" />
      <path d="M9 17a4 4 0 0 0 4 4h1a4 4 0 0 0 4-4v-3m-2 0h4" />
    </template>
    <template v-else-if="name === 'plus'">
      <path d="M12 5v14M5 12h14" />
    </template>
    <template v-else-if="name === 'home'">
      <path d="m3 11 9-7 9 7" />
      <path d="M5 10v10h14V10M9 20v-6h6v6" />
    </template>
    <template v-else-if="name === 'swap'">
      <path d="M4 7h14m-3-3 3 3-3 3M20 17H6m3 3-3-3 3-3" />
    </template>
    <template v-else-if="name === 'sparkle'">
      <path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z" />
      <path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15ZM5 3l.6 1.4L7 5l-1.4.6L5 7l-.6-1.4L3 5l1.4-.6L5 3Z" />
    </template>
    <template v-else-if="name === 'check'">
      <path d="m5 12 4 4L19 6" />
    </template>
    <template v-else-if="name === 'package'">
      <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" />
      <path d="m4.5 7.8 7.5 4.3 7.5-4.3M12 12v9M8 5.2l8 4.5" />
    </template>
    <template v-else-if="name === 'refresh'">
      <path d="M20 7v5h-5" />
      <path d="M18.5 16a8 8 0 1 1 .8-7L20 12" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </template>
    <template v-else-if="name === 'alert'">
      <path d="M10.3 4.3 2.8 18a2 2 0 0 0 1.8 3h14.8a2 2 0 0 0 1.8-3L13.7 4.3a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4m0 4h.01" />
    </template>
    <template v-else-if="name === 'user'">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </template>
    <template v-else-if="name === 'arrow-right'">
      <path d="M5 12h14m-5-5 5 5-5 5" />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6m0-10h.01" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.7 9a2.5 2.5 0 1 1 3.7 2.2c-.9.5-1.4 1-1.4 2.3m0 3.5h.01" />
    </template>
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  strokeWidth: { type: [Number, String], default: 1.8 },
  label: { type: String, default: '' }
})
</script>

<style scoped>
.app-icon {
  display: block;
  flex: 0 0 auto;
}
</style>
