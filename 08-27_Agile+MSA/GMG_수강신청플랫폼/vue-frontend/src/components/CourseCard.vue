<template>
  <router-link
    :to="`/groups/${groupId}/assets/${course.id}`"
    class="gear-card surface"
    :aria-label="`${course.title}, ${availabilityLabel}, 최대 ${course.maxLoanDays || 7}일 대여`"
  >
    <div class="card-visual" :class="toneClass">
      <div class="category-mark" aria-hidden="true">
        <AppIcon :name="icon" :size="36" class="category-icon" />
        <small>{{ shortCategory }}</small>
      </div>
      <span :class="['stock-pill', { empty: available === 0 }]">{{ availabilityLabel }}</span>
    </div>

    <div class="card-body">
      <div class="scope-line">
        <span class="badge">{{ course.category }}</span>
        <span :class="['scope-badge', course.visibility === 'ORGANIZATION' ? 'organization' : 'group']">
          {{ course.visibility === 'ORGANIZATION' ? '학교 공용' : '그룹 전용' }}
        </span>
      </div>
      <h3>{{ course.title }}</h3>
      <p>{{ course.description || '수업, 연구와 그룹 활동에 사용할 수 있는 자산입니다.' }}</p>
      <dl class="card-meta">
        <div>
          <dt>수령, 반납</dt>
          <dd>{{ course.pickupLocation || '그룹 운영실' }}</dd>
        </div>
        <div>
          <dt>최대 기간</dt>
          <dd>{{ course.maxLoanDays || 7 }}일</dd>
        </div>
      </dl>
      <div class="card-action">
        <span>{{ available > 0 ? '상세 확인 후 신청' : '반납 후 신청 가능' }}</span>
        <b aria-hidden="true">→</b>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { categoryIcon } from '@/store/course.js'

const props = defineProps({
  course: { type: Object, required: true },
  groupId: { type: [String, Number], required: true }
})

const available = computed(() => Number(props.course.availableQuantity ?? 0))
const icon = computed(() => categoryIcon(props.course.categoryCode || props.course.category))
const shortCategory = computed(() => String(props.course.category || '기타').slice(0, 6))
const toneClass = computed(() => `tone-${(props.course.categoryCode || 'ETC').toLowerCase().replaceAll('_', '-')}`)
const availabilityLabel = computed(() => available.value > 0 ? `${available.value}개 가능` : '현재 대여 불가')
</script>

<style scoped>
.gear-card {
  overflow: hidden;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.gear-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-md);
}
.card-visual {
  min-height: 104px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 15px;
  background: linear-gradient(145deg, #f1f6ff, #e4edfb);
}
.tone-computer { background: linear-gradient(145deg, #eef5ff, #dfeafb); }
.tone-camera-audio { background: linear-gradient(145deg, #f3f7ff, #e5edfa); }
.tone-presentation { background: linear-gradient(145deg, #edf4ff, #dae8fc); }
.tone-maker { background: linear-gradient(145deg, #f0f5fd, #e0e9f7); }
.tone-electronics-iot { background: linear-gradient(145deg, #eaf3ff, #d9e8fc); }
.tone-device { background: linear-gradient(145deg, #eef5ff, #dfeafa); }
.tone-accessory { background: linear-gradient(145deg, #f2f6fc, #e4ebf6); }
.category-mark {
  align-self: center;
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(16, 42, 67, .76);
}
.category-icon { color: var(--color-primary-dark); }
.category-mark small {
  max-width: 74px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .08em;
}
.stock-pill {
  padding: 5px 8px;
  color: var(--color-success);
  background: rgba(255, 255, 255, .9);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}
.stock-pill.empty { color: var(--color-danger); }
.card-body { padding: 18px; }
.scope-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.scope-badge {
  font-size: 10px;
  font-weight: 700;
}
.scope-badge.organization { color: var(--color-info); }
.scope-badge.group { color: var(--color-ai); }
h3 {
  margin-top: 10px;
  color: var(--color-navy);
  font-size: 17px;
  line-height: 1.35;
}
p {
  min-height: 43px;
  margin-top: 7px;
  display: -webkit-box;
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.card-meta {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  margin-top: 15px;
  padding-top: 13px;
  border-top: 1px solid var(--color-border);
}
.card-meta div { min-width: 0; }
.card-meta dt {
  color: var(--color-text-muted);
  font-size: 10px;
}
.card-meta dd {
  margin: 2px 0 0;
  overflow: hidden;
  font-size: 11px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-meta div:last-child { text-align: right; }
.card-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 13px;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}
.card-action b { font-size: 15px; }
</style>
