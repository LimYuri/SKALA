<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <router-link :to="path('/assets')" class="back-link">← 자산 목록</router-link>

        <div v-if="loading" class="loading-state surface">
          <div class="spinner"></div>
          <span>자산 정보와 내 요청을 확인하고 있습니다.</span>
        </div>

        <div v-else-if="course" class="detail-grid fade-in-up">
          <section class="detail-main">
            <div class="gear-visual" :class="`tone-${(course.categoryCode || 'etc').toLowerCase()}`">
              <span aria-hidden="true"><AppIcon :name="categoryIcon(course.categoryCode || course.category)" :size="82" :stroke-width="1.25" /></span>
              <div class="asset-number">ASSET #{{ String(course.id).padStart(4, '0') }}</div>
              <div class="visual-scope">{{ scopeLabel }}</div>
            </div>

            <div class="detail-copy surface">
              <div class="tag-row">
                <span class="badge">{{ course.category }}</span>
                <span :class="['scope', course.visibility === 'ORGANIZATION' ? 'organization' : 'group']">
                  {{ scopeLabel }}
                </span>
              </div>
              <h1>{{ course.title }}</h1>
              <p>{{ course.description || '수업, 연구와 그룹 활동에 사용할 수 있는 자산입니다.' }}</p>

              <dl class="spec-grid">
                <div><dt>전체 수량</dt><dd>{{ course.totalQuantity }}개</dd></div>
                <div><dt>가용 수량</dt><dd :class="{ danger: available === 0 }">{{ available }}개</dd></div>
                <div><dt>수령, 반납 장소</dt><dd>{{ course.pickupLocation || '그룹 운영실' }}</dd></div>
                <div><dt>최대 대여</dt><dd>{{ course.maxLoanDays || 7 }}일</dd></div>
              </dl>
            </div>

            <section class="loan-guide surface">
              <div>
                <span>1</span>
                <strong>기간과 목적 입력</strong>
                <p>필요한 일정과 구체적인 활용 목적을 적습니다.</p>
              </div>
              <i aria-hidden="true">→</i>
              <div>
                <span>2</span>
                <strong>그룹 관리자 승인</strong>
                <p>승인 시 재고 1개가 배정됩니다.</p>
              </div>
              <i aria-hidden="true">→</i>
              <div>
                <span>3</span>
                <strong>반납 확인</strong>
                <p>장비 전달 후 확인되면 재고가 복원됩니다.</p>
              </div>
            </section>
          </section>

          <aside class="request-panel surface">
            <div class="panel-heading">
              <div>
                <span class="panel-label">LOAN REQUEST</span>
                <h2>대여 신청</h2>
              </div>
              <span :class="['stock-state', { out: available === 0 }]">
                {{ available > 0 ? `${available}개 가능` : '재고 없음' }}
              </span>
            </div>

            <div v-if="openRequest" class="existing-request">
              <div class="existing-heading">
                <StatusBadge :status="openRequest.status" />
                <span>REQ-{{ String(openRequest.id).padStart(4, '0') }}</span>
              </div>
              <h3>이미 진행 중인 요청이 있습니다.</h3>
              <p>
                <strong>{{ requestGroupName }}</strong>에서 같은 자산을 처리 중입니다.
                중복 대여를 막기 위해 새 신청은 잠시 제한됩니다.
              </p>
              <RequestProgress :type="openRequest.requestType" :status="openRequest.status" />
              <router-link :to="`/groups/${openRequest.groupId}/loans`" class="btn btn-outline btn-block">
                진행 중인 요청 보기
              </router-link>
            </div>

            <template v-else>
              <div class="date-grid">
                <label class="field">
                  <span>대여 시작일</span>
                  <input v-model="form.requestedFrom" type="date" :min="today" class="form-input" />
                </label>
                <label class="field">
                  <span>반납 예정일</span>
                  <input
                    v-model="form.dueDate"
                    type="date"
                    :min="form.requestedFrom"
                    :max="maxDueDate"
                    class="form-input"
                  />
                </label>
              </div>

              <div class="duration-summary">
                <span>선택 기간</span>
                <strong>{{ durationDays }}일</strong>
                <small>최대 {{ course.maxLoanDays || 7 }}일</small>
              </div>

              <label class="field reason-field">
                <span>사용 목적</span>
                <textarea
                  v-model.trim="form.reason"
                  class="form-textarea"
                  placeholder="수업명, 연구, 행사 목적과 사용 장소를 구체적으로 적어 주세요."
                  maxlength="500"
                ></textarea>
                <small class="character-count">{{ form.reason.length }}/500</small>
              </label>
            </template>

            <div v-if="message" class="success-box" role="status">{{ message }}</div>
            <div v-if="error" class="error-box" role="alert">{{ error }}</div>

            <button
              v-if="!openRequest"
              class="btn btn-primary btn-block"
              :disabled="submitting || available === 0"
              @click="submitLoan"
            >
              {{ submitting ? '신청 중...' : '대여 신청하기' }}
            </button>
            <p class="helper">승인 전에는 재고가 차감되지 않으며, 반납도 관리자 확인 후 완료됩니다.</p>
          </aside>
        </div>

        <div v-else class="empty-state surface">
          <strong>자산 정보를 찾을 수 없습니다.</strong>
          <router-link :to="path('/assets')" class="btn btn-outline">자산 목록</router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import RequestProgress from '@/components/RequestProgress.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { enrollmentApi } from '@/api/enrollment.js'
import { categoryIcon, useCourseStore } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'
import { isOpenRequest } from '@/utils/requestStatus.js'

const route = useRoute()
const courseStore = useCourseStore()
const groupStore = useGroupStore()
const error = ref('')
const message = ref('')
const submitting = ref(false)
const requests = ref([])

const groupId = computed(() => Number(route.params.groupId))
const course = computed(() => courseStore.selectedCourse)
const loading = computed(() => courseStore.loading)
const available = computed(() => Number(course.value?.availableQuantity ?? 0))
const scopeLabel = computed(() => course.value?.visibility === 'ORGANIZATION' ? '학교 공용' : '그룹 전용')

const asIso = date => {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}
const today = asIso(new Date())
const form = reactive({ requestedFrom: today, dueDate: today, reason: '' })

const openRequest = computed(() => requests.value.find(item => (
  Number(item.courseId) === Number(course.value?.id) && isOpenRequest(item.status)
)))
const requestGroupName = computed(() => (
  groupStore.groups.find(group => Number(group.id) === Number(openRequest.value?.groupId))?.name
  || `그룹 #${openRequest.value?.groupId}`
))
const maxDueDate = computed(() => {
  if (!form.requestedFrom) return today
  const start = new Date(`${form.requestedFrom}T00:00:00`)
  start.setDate(start.getDate() + Math.max(1, Number(course.value?.maxLoanDays || 7)) - 1)
  return asIso(start)
})
const durationDays = computed(() => {
  const start = new Date(`${form.requestedFrom}T00:00:00`)
  const due = new Date(`${form.dueDate}T00:00:00`)
  if (Number.isNaN(start.getTime()) || Number.isNaN(due.getTime())) return 0
  return Math.max(0, Math.floor((due - start) / 86400000) + 1)
})

const path = suffix => `/groups/${groupId.value}${suffix}`

function explain(cause) {
  return cause.response?.data?.message
    || cause.response?.data?.detail
    || cause.response?.data?.error
    || '대여 신청을 처리하지 못했습니다.'
}

function validate() {
  if (!form.requestedFrom || !form.dueDate) return '대여 시작일과 반납 예정일을 선택해 주세요.'
  if (form.requestedFrom < today) return '대여 시작일은 오늘 이후여야 합니다.'
  if (form.dueDate < form.requestedFrom) return '반납 예정일은 대여 시작일 이후여야 합니다.'
  if (form.dueDate > maxDueDate.value) return `최대 ${course.value.maxLoanDays || 7}일까지 대여할 수 있습니다.`
  if (!form.reason || form.reason.length < 5) return '사용 목적을 5자 이상 구체적으로 입력해 주세요.'
  return ''
}

async function submitLoan() {
  error.value = validate()
  message.value = ''
  if (error.value) return

  submitting.value = true
  try {
    const response = await enrollmentApi.enroll({
      courseId: course.value.id,
      groupId: groupId.value,
      ...form
    })
    requests.value.unshift(response.data?.data)
    form.reason = ''
    message.value = '대여 신청을 보냈습니다. 관리자 승인 전까지 재고는 유지됩니다.'
  } catch (cause) {
    error.value = explain(cause)
  } finally {
    submitting.value = false
  }
}

async function load() {
  error.value = ''
  message.value = ''
  await Promise.all([
    courseStore.fetchCourse(route.params.id),
    groupStore.fetchGroups().catch(() => [])
  ])

  const days = Math.min(7, Number(course.value?.maxLoanDays || 7))
  const due = new Date()
  due.setDate(due.getDate() + days - 1)
  form.requestedFrom = today
  form.dueDate = asIso(due)

  try {
    const response = await enrollmentApi.getMyEnrollments()
    requests.value = response.data?.data ?? []
  } catch {
    requests.value = []
  }
}

watch(() => route.params.id, load)
onMounted(load)
</script>

<style scoped>
.back-link {
  display: inline-flex;
  margin-bottom: 20px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 650;
}
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 390px;
  gap: 22px;
  align-items: start;
}
.detail-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.gear-visual {
  position: relative;
  min-height: 260px;
  display: grid;
  place-items: center;
  color: rgba(29, 78, 216, .78);
  background: linear-gradient(145deg, #eaf2ff, #f4f7fd);
  border-radius: var(--radius-xl);
  overflow: hidden;
}
.gear-visual::before,
.gear-visual::after {
  content: '';
  position: absolute;
  border: 1px solid rgba(16, 42, 67, .08);
  border-radius: 50%;
}
.gear-visual::before { width: 310px; height: 310px; }
.gear-visual::after { width: 190px; height: 190px; }
.gear-visual > span {
  z-index: 1;
}
.asset-number,
.visual-scope {
  position: absolute;
  bottom: 17px;
  z-index: 1;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .12em;
}
.asset-number { left: 20px; }
.visual-scope {
  right: 20px;
  padding: 5px 8px;
  background: rgba(255, 255, 255, .75);
  border-radius: 999px;
  letter-spacing: 0;
}
.detail-copy { padding: 28px; }
.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.scope {
  font-size: 10px;
  font-weight: 750;
}
.scope.organization { color: var(--color-info); }
.scope.group { color: var(--color-ai); }
.detail-copy h1 {
  margin-top: 13px;
  color: var(--color-navy);
  font-size: clamp(26px, 3vw, 32px);
  letter-spacing: -.04em;
}
.detail-copy > p {
  margin-top: 10px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.8;
}
.spec-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}
.spec-grid div { min-width: 0; }
.spec-grid dt {
  color: var(--color-text-muted);
  font-size: 10px;
}
.spec-grid dd {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 750;
  word-break: keep-all;
}
.danger { color: var(--color-danger); }
.loan-guide {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 13px;
  padding: 21px;
}
.loan-guide div {
  display: grid;
  grid-template-columns: 28px 1fr;
  column-gap: 9px;
}
.loan-guide div > span {
  grid-row: 1 / 3;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 800;
}
.loan-guide strong { font-size: 11px; }
.loan-guide p {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 9px;
  line-height: 1.5;
}
.loan-guide i { color: #8399b9; }
.request-panel {
  position: sticky;
  top: 90px;
  padding: 25px;
}
.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.panel-label {
  color: var(--color-primary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .15em;
}
.request-panel h2 {
  margin-top: 5px;
  color: var(--color-navy);
  font-size: 22px;
}
.stock-state {
  padding: 6px 9px;
  color: var(--color-success);
  background: var(--color-success-light);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}
.stock-state.out {
  color: var(--color-danger);
  background: var(--color-danger-light);
}
.date-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 20px;
}
.date-grid .form-input {
  padding-inline: 8px;
  font-size: 11px;
}
.duration-summary {
  display: flex;
  align-items: baseline;
  gap: 7px;
  margin-top: 10px;
  padding: 9px 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  border-radius: 9px;
  font-size: 10px;
}
.duration-summary strong {
  color: var(--color-primary);
  font-size: 14px;
}
.duration-summary small { margin-left: auto; }
.reason-field {
  position: relative;
  margin: 14px 0;
}
.reason-field textarea {
  min-height: 120px;
  padding-bottom: 28px;
}
.character-count {
  position: absolute;
  right: 10px;
  bottom: 7px;
  color: var(--color-text-muted);
  font-size: 9px;
}
.existing-request {
  display: flex;
  flex-direction: column;
  gap: 13px;
  margin-top: 20px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: 13px;
}
.existing-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.existing-heading > span {
  color: var(--color-text-muted);
  font-size: 9px;
  font-weight: 750;
}
.existing-request h3 {
  color: var(--color-navy);
  font-size: 14px;
}
.existing-request p {
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1.65;
}
.helper {
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 10px;
  line-height: 1.55;
  text-align: center;
}
.success-box,
.error-box { margin: 12px 0; }

@media (max-width: 900px) {
  .detail-grid { grid-template-columns: 1fr; }
  .request-panel { position: static; }
}
@media (max-width: 620px) {
  .spec-grid { grid-template-columns: repeat(2, 1fr); }
  .date-grid { grid-template-columns: 1fr; }
  .loan-guide { grid-template-columns: 1fr; }
  .loan-guide i { display: none; }
}
</style>
