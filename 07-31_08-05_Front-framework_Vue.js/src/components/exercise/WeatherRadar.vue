<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { fetchRadarFrames } from '@/services/weatherApi'

const props = defineProps({ latitude: { type: Number, required: true }, longitude: { type: Number, required: true }, cityName: { type: String, required: true } })
const mapElement = ref(null)
const frames = ref([])
const frameIndex = ref(0)
const radarHost = ref('')
const errorMessage = ref('')
const isPlaying = ref(false)
let map
let radarLayer
let playTimer

const currentFrame = computed(() => frames.value[frameIndex.value])
const frameTime = computed(() => (currentFrame.value ? new Intl.DateTimeFormat('ko-KR', { hour: '2-digit', minute: '2-digit' }).format(new Date(currentFrame.value.time * 1000)) : '-'))

function drawFrame() {
  if (!map || !currentFrame.value) return
  if (radarLayer) radarLayer.remove()
  radarLayer = L.tileLayer(`${radarHost.value}${currentFrame.value.path}/256/{z}/{x}/{y}/2/1_1.png`, { opacity: 0.72, maxNativeZoom: 7, maxZoom: 12, attribution: 'Radar © RainViewer' }).addTo(map)
}
watch(frameIndex, drawFrame)

function togglePlayback() {
  isPlaying.value = !isPlaying.value
  clearInterval(playTimer)
  if (isPlaying.value)
    playTimer = setInterval(() => {
      frameIndex.value = (frameIndex.value + 1) % frames.value.length
    }, 900)
}

async function initializeRadar() {
  try {
    const data = await fetchRadarFrames()
    radarHost.value = data.host
    frames.value = data.frames
    frameIndex.value = frames.value.length - 1
    await nextTick()
    map = L.map(mapElement.value, { zoomControl: true, scrollWheelZoom: false }).setView([props.latitude, props.longitude], 7)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: 'Map © OpenStreetMap contributors' }).addTo(map)
    L.circleMarker([props.latitude, props.longitude], { radius: 7, color: '#fff', weight: 3, fillColor: '#ef4444', fillOpacity: 1 }).addTo(map).bindTooltip(props.cityName)
    drawFrame()
  } catch (error) {
    console.error(error)
    errorMessage.value = '현재 레이더 영상을 불러오지 못했습니다. 잠시 후 다시 확인해 주세요.'
  }
}

onMounted(initializeRadar)
onBeforeUnmount(() => {
  clearInterval(playTimer)
  map?.remove()
})
</script>

<template>
  <section class="radar-section" aria-labelledby="radar-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">비구름 레이더</p>
        <h2 id="radar-title">{{ cityName }} 주변 강수 레이더</h2>
      </div>
      <span v-if="currentFrame">{{ frameTime }} 기준</span>
    </div>
    <p class="radar-description">최근 레이더 프레임을 재생해 비구름의 이동을 확인할 수 있습니다. 지도 확대·축소와 이동도 가능합니다.</p>
    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
    <template v-else>
      <div ref="mapElement" class="radar-map" aria-label="강수 레이더 지도"></div>
      <div v-if="frames.length" class="radar-controls">
        <button class="button secondary" @click="togglePlayback">{{ isPlaying ? '일시정지' : '레이더 재생' }}</button>
        <input v-model.number="frameIndex" type="range" min="0" :max="frames.length - 1" aria-label="레이더 시간 선택" />
        <span>{{ frameIndex + 1 }} / {{ frames.length }}</span>
      </div>
    </template>
    <p class="source-note">
      레이더: <a href="https://www.rainviewer.com/" target="_blank" rel="noreferrer">RainViewer</a> · 지도: OpenStreetMap · 레이더 관측 범위 밖에서는 영상이 표시되지 않을 수 있습니다.
    </p>
  </section>
</template>
