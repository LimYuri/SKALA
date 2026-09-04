<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <div class="page-heading">
          <div>
            <span class="eyebrow">MY REQUESTS</span>
            <p class="page-subtitle">요청별 진행 단계와 다음 행동을 확인하고, 대여 중인 장비를 반납할 수 있습니다.</p>
          </div>
          <router-link :to="path('/assets')" class="btn btn-primary">새 대여 신청</router-link>
        </div>

        <section class="request-summary" aria-label="요청 현황">
          <button :class="{ active: statusFilter === 'PENDING' }" :aria-pressed="statusFilter === 'PENDING'" @click="toggleStatus('PENDING')">
            <span class="summary-icon pending" aria-hidden="true"><AppIcon name="info" :size="20" /></span>
            <div><small>검토 대기</small><strong>{{ pendingCount }}</strong></div>
          </button>
          <button :class="{ active: statusFilter === 'ACTIVE' }" :aria-pressed="statusFilter === 'ACTIVE'" @click="toggleStatus('ACTIVE')">
            <span class="summary-icon active" aria-hidden="true"><AppIcon name="swap" :size="20" /></span>
            <div><small>대여 중</small><strong>{{ activeCount }}</strong></div>
          </button>
          <button :class="{ active: statusFilter === 'RETURN_REQUESTED' }" :aria-pressed="statusFilter === 'RETURN_REQUESTED'" @click="toggleStatus('RETURN_REQUESTED')">
            <span class="summary-icon return" aria-hidden="true"><AppIcon name="check" :size="20" /></span>
            <div><small>반납 확인 대기</small><strong>{{ returnCount }}</strong></div>
          </button>
          <button :class="{ active: statusFilter === 'OVERDUE' }" :aria-pressed="statusFilter === 'OVERDUE'" @click="toggleStatus('OVERDUE')">
            <span class="summary-icon overdue" aria-hidden="true"><AppIcon name="alert" :size="20" /></span>
            <div><small>연체</small><strong>{{ overdueCount }}</strong></div>
          </button>
        </section>

        <div v-if="message" class="success-box feedback" role="status">{{ message }}</div>
        <div v-if="error" class="error-box feedback" role="alert">{{ error }}</div>

        <section class="request-toolbar surface" aria-label="요청 필터">
          <div class="type-tabs" role="tablist">
            <button
              v-for="type in requestTypes"
              :key="type.value"
              role="tab"
              :aria-selected="tab === type.value"
              :class="{ active: tab === type.value }"
              @click="tab = type.value"
            >
              {{ type.label }} <span>{{ countType(type.value) }}</span>
            </button>
          </div>
          <label>
            <span>상태</span>
            <select v-model="statusFilter" aria-label="요청 상태">
              <option value="ALL">전체 상태</option>
              <option value="OPEN">진행 중</option>
              <option value="PENDING">검토 대기</option>
              <option value="ACTIVE">대여 중</option>
              <option value="RETURN_REQUESTED">반납 확인 대기</option>
              <option value="COMPLETED">완료</option>
              <option value="REJECTED">반려</option>
              <option value="OVERDUE">연체</option>
            </select>
          </label>
        </section>

        <div v-if="loading" class="loading-state surface">
          <div class="spinner"></div>
          <span>요청 이력을 불러오고 있습니다.</span>
        </div>

        <div v-else-if="filtered.length" class="request-list">
          <article
            v-for="item in filtered"
            :key="item.id"
            class="request-card surface"
            :class="{ overdue: item.overdue }"
          >
            <div class="request-top">
              <div class="request-identity">
                <router-link :to="path(`/assets/${item.courseId}`)" class="asset-symbol" aria-label="자산 상세">
                  <AppIcon :name="categoryIcon(item.course?.category)" :size="22" />
                </router-link>
                <div>
                  <div class="title-row">
                    <StatusBadge :status="item.status" />
                    <span v-if="item.overdue" class="overdue-pill">연체</span>
                    <span class="request-number">REQ-{{ String(item.id).padStart(4, '0') }}</span>
                  </div>
                  <h2>{{ item.course?.title || `자산 #${item.courseId}` }}</h2>
                  <p>{{ item.reason || '요청 사유가 없습니다.' }}</p>
                </div>
              </div>

              <div class="request-actions">
                <button
                  v-if="item.requestType === 'LOAN' && item.status === 'ACTIVE'"
                  class="btn btn-primary btn-sm"
                  :disabled="busyId === item.id"
                  @click="askReturn(item)"
                >
                  반납 요청
                </button>
                <span v-else class="next-step">{{ statusMeta(item.status).next }}</span>
              </div>
            </div>

            <dl class="request-meta">
              <div>
                <dt>요청 유형</dt>
                <dd>{{ item.requestType === 'LOAN' ? '장비 대여' : '미보유 장비 도입' }}</dd>
              </div>
              <div v-if="item.requestedFrom">
                <dt>이용 기간</dt>
                <dd>{{ shortDate(item.requestedFrom) }} → {{ shortDate(item.dueDate) }}</dd>
              </div>
              <div v-if="item.status === 'ACTIVE' && item.dueDate">
                <dt>반납까지</dt>
                <dd :class="{ danger: dueDays(item) < 0 }">{{ dueLabel(item) }}</dd>
              </div>
              <div>
                <dt>신청 시각</dt>
                <dd>{{ dateTime(item.createdAt) }}</dd>
              </div>
              <div v-if="item.course?.pickupLocation">
                <dt>수령, 반납</dt>
                <dd>{{ item.course.pickupLocation }}</dd>
              </div>
            </dl>

            <div v-if="item.reviewComment" class="review-comment">
              <strong>관리자 검토 의견</strong>
              <p>{{ item.reviewComment }}</p>
            </div>

            <RequestProgress :type="item.requestType" :status="item.status" />
          </article>
        </div>

        <div v-else class="empty-state surface">
          <span class="empty-icon"><AppIcon name="swap" :size="30" /></span>
          <strong>{{ emptyTitle }}</strong>
          <p>상태 필터를 바꾸거나 새로운 요청을 시작해 보세요.</p>
          <router-link :to="tab === 'LOAN' ? path('/assets') : path('/acquisitions/new')" class="btn btn-outline">
            새 요청 시작
          </router-link>
        </div>
      </div>
    </main>

    <ConfirmDialog
      :open="!!returnTarget"
      title="장비를 반납 요청할까요?"
      :description="returnDescription"
      confirm-label="반납 요청 보내기"
      @cancel="returnTarget = null"
      @confirm="requestReturn"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import RequestProgress from '@/components/RequestProgress.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { enrollmentApi } from '@/api/enrollment.js'
import { categoryIcon } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'
import { daysUntil, formatApiDateTime, formatLocalDate } from '@/utils/datetime.js'
import { isOpenRequest, statusMeta } from '@/utils/requestStatus.js'

const route = useRoute()
const groupStore = useGroupStore()
const groupId = computed(() => Number(route.params.groupId))
const items = ref([])
const loading = ref(true)
const tab = ref(route.query.type === 'PURCHASE' ? 'PURCHASE' : 'LOAN')
const statusFilter = ref('ALL')
const busyId = ref(null)
const error = ref('')
const message = ref('')
const returnTarget = ref(null)

const requestTypes = [
  { value: 'LOAN', label: '대여' },
  { value: 'PURCHASE', label: '도입' }
]

const pendingCount = computed(() => items.value.filter(item => ['PENDING', 'GROUP_APPROVED', 'BUDGET_APPROVED'].includes(item.status)).length)
const activeCount = computed(() => items.value.filter(item => item.requestType === 'LOAN' && item.status === 'ACTIVE').length)
const returnCount = computed(() => items.value.filter(item => item.status === 'RETURN_REQUESTED').length)
const overdueCount = computed(() => items.value.filter(item => item.overdue).length)

const filtered = computed(() => items.value.filter(item => {
  if (item.requestType !== tab.value) return false
  if (statusFilter.value === 'ALL') return true
  if (statusFilter.value === 'OPEN') return isOpenRequest(item.status)
  if (statusFilter.value === 'COMPLETED') return ['RETURNED', 'RECEIVED'].includes(item.status)
  if (statusFilter.value === 'OVERDUE') return item.overdue
  return item.status === statusFilter.value
}))

const emptyTitle = computed(() => (
  statusFilter.value === 'ALL'
    ? (tab.value === 'LOAN' ? '대여 요청이 없습니다.' : '도입 요청이 없습니다.')
    : '선택한 상태의 요청이 없습니다.'
))
const returnDescription = computed(() => {
  if (!returnTarget.value) return ''
  const location = returnTarget.value.course?.pickupLocation || '그룹 운영실'
  return `${returnTarget.value.course?.title || '장비'}를 ${location}에 전달한 뒤 요청해 주세요. 관리자가 확인하기 전까지 재고는 복원되지 않습니다.`
})

const path = suffix => `/groups/${groupId.value}${suffix}`
const countType = type => items.value.filter(item => item.requestType === type).length
const shortDate = value => formatLocalDate(value)
const dateTime = value => formatApiDateTime(value)
const dueDays = item => daysUntil(item.dueDate)
const dueLabel = item => {
  const days = dueDays(item)
  if (days == null) return '-'
  if (days < 0) return `${Math.abs(days)}일 연체`
  if (days === 0) return '오늘 반납'
  return `D-${days}`
}

function toggleStatus(status) {
  statusFilter.value = statusFilter.value === status ? 'ALL' : status
  if (status === 'ACTIVE' || status === 'RETURN_REQUESTED' || status === 'OVERDUE') tab.value = 'LOAN'
}

function askReturn(item) {
  returnTarget.value = item
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    await groupStore.loadGroup(groupId.value)
    const response = await enrollmentApi.getMyEnrollments(groupId.value)
    items.value = (response.data?.data ?? []).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
  } catch (cause) {
    error.value = cause.response?.data?.message || '요청 목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function requestReturn() {
  const item = returnTarget.value
  if (!item) return
  busyId.value = item.id
  error.value = ''
  message.value = ''
  returnTarget.value = null

  try {
    const response = await enrollmentApi.requestReturn(item.id)
    Object.assign(item, response.data?.data)
    message.value = '반납 요청을 보냈습니다. 장비 전달 후 관리자가 상태와 구성품을 확인합니다.'
  } catch (cause) {
    error.value = cause.response?.data?.message || cause.response?.data?.error || '반납 요청에 실패했습니다.'
  } finally {
    busyId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.request-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.request-summary button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 17px;
  text-align: left;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.request-summary button.active {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, .08);
}
.summary-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  font-size: 15px;
  font-weight: 800;
}
.summary-icon.pending { color: var(--color-warning); background: var(--color-warning-light); }
.summary-icon.active { color: var(--color-success); background: var(--color-success-light); }
.summary-icon.return { color: var(--color-info); background: var(--color-info-light); }
.summary-icon.overdue { color: var(--color-danger); background: var(--color-danger-light); }
.request-summary button > div {
  display: flex;
  flex-direction: column;
}
.request-summary small {
  color: var(--color-text-muted);
  font-size: 11px;
}
.request-summary strong {
  color: var(--color-navy);
  font-size: 22px;
  line-height: 1.25;
}
.feedback { margin-bottom: 14px; }
.request-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  padding: 10px 12px;
}
.type-tabs {
  display: flex;
  gap: 7px;
}
.type-tabs button {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 38px;
  padding: 8px 14px;
  color: var(--color-text-secondary);
  background: transparent;
  border: 0;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 750;
}
.type-tabs button.active {
  color: #fff;
  background: var(--color-primary);
}
.type-tabs span { opacity: .75; }
.request-toolbar > label {
  display: flex;
  align-items: center;
  gap: 8px;
}
.request-toolbar > label span {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
}
.request-toolbar select {
  height: 38px;
  padding: 0 10px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 9px;
  font-size: 11px;
}
.request-list {
  display: flex;
  flex-direction: column;
  gap: 13px;
}
.request-card {
  padding: 20px;
}
.request-card.overdue {
  border-left: 4px solid var(--color-danger);
}
.request-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.request-identity {
  min-width: 0;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 14px;
}
.asset-symbol {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 14px;
  font-size: 21px;
}
.title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.overdue-pill {
  padding: 5px 8px;
  color: #fff;
  background: var(--color-danger);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}
.request-number {
  color: var(--color-text-muted);
  font-size: 9px;
  font-weight: 750;
}
.request-identity h2 {
  margin-top: 7px;
  color: var(--color-navy);
  font-size: 17px;
}
.request-identity p {
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.request-actions {
  max-width: 210px;
  text-align: right;
}
.next-step {
  color: var(--color-text-muted);
  font-size: 10px;
  line-height: 1.55;
}
.request-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  margin: 17px 0;
  padding: 13px 14px;
  background: var(--color-bg-secondary);
  border-radius: 10px;
}
.request-meta div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.request-meta dt {
  color: var(--color-text-muted);
  font-size: 9px;
}
.request-meta dd {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
}
.request-meta .danger { color: var(--color-danger); }
.review-comment {
  margin-bottom: 14px;
  padding: 11px 13px;
  color: var(--color-danger);
  background: var(--color-danger-light);
  border-radius: 9px;
}
.review-comment strong { font-size: 10px; }
.review-comment p { margin-top: 3px; font-size: 11px; }

@media (max-width: 800px) {
  .request-summary { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 620px) {
  .request-toolbar,
  .request-top {
    align-items: stretch;
    flex-direction: column;
  }
  .request-actions {
    max-width: none;
    padding-left: 66px;
    text-align: left;
  }
  .request-actions .btn { width: 100%; }
  .request-summary button { padding: 13px; }
}
</style>
