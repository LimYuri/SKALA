<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <template v-if="isManager">
          <div class="page-heading">
            <div>
              <span class="eyebrow">GROUP OPERATIONS DESK</span>
              <h1 class="page-title">운영 데스크</h1>
            </div>
            <button class="btn btn-ghost" :disabled="loading" @click="loadAll">
              <AppIcon name="refresh" :size="15" />
              {{ loading ? '불러오는 중...' : '새로고침' }}
            </button>
          </div>

          <section class="admin-summary" aria-label="처리 대기 현황">
            <button type="button" :class="{ active: tab === 'loan' }" :aria-pressed="tab === 'loan'" @click="setTab('loan')">
              <span class="summary-mark green"><AppIcon name="swap" :size="18" /></span>
              <div><small>대여 승인</small><strong>{{ loans.length }}</strong></div>
            </button>
            <button type="button" :class="{ active: tab === 'return' }" :aria-pressed="tab === 'return'" @click="setTab('return')">
              <span class="summary-mark blue"><AppIcon name="check" :size="18" /></span>
              <div><small>반납 확인</small><strong>{{ returns.length }}</strong></div>
            </button>
            <button type="button" :class="{ active: tab === 'acquisition' }" :aria-pressed="tab === 'acquisition'" @click="setTab('acquisition')">
              <span class="summary-mark amber"><AppIcon name="plus" :size="18" /></span>
              <div><small>도입 필요성</small><strong>{{ acquisitions.length }}</strong></div>
            </button>
            <button type="button" :class="{ active: tab === 'intake' }" :aria-pressed="tab === 'intake'" @click="setTab('intake')">
              <span class="summary-mark purple"><AppIcon name="package" :size="18" /></span>
              <div><small>입고 대기</small><strong>{{ intake.length }}</strong></div>
            </button>
          </section>

          <div v-if="message" class="success-box feedback" role="status">{{ message }}</div>
          <div v-if="error" class="error-box feedback" role="alert">{{ error }}</div>

          <section class="queue-toolbar surface">
            <div class="tabs" role="tablist">
              <button
                v-for="item in tabs"
                :key="item.key"
                role="tab"
                :aria-selected="tab === item.key"
                :class="{ active: tab === item.key }"
                @click="setTab(item.key)"
              >
                {{ item.label }} <span>{{ item.count }}</span>
              </button>
            </div>
            <label class="queue-search">
              <span class="sr-only">요청 검색</span>
              <span class="queue-search-icon"><AppIcon name="search" :size="16" /></span>
              <input v-model.trim="keyword" type="search" placeholder="자산명, 요청자, 사유 검색" />
            </label>
          </section>

          <div v-if="loading" class="loading-state surface">
            <div class="spinner"></div>
            <span>운영 대기열과 요청자 정보를 불러오고 있습니다.</span>
          </div>

          <div v-else-if="filteredItems.length" class="approval-list">
            <article
              v-for="item in filteredItems"
              :key="item.id ?? item.paymentId"
              class="approval-card surface"
            >
              <div class="request-header">
                <div>
                  <span class="request-type">{{ tabLabel }}, {{ requestNumber(item) }}</span>
                  <h2>{{ item.course?.title || `자산 #${item.courseId}` }}</h2>
                </div>
                <span class="queue-age">{{ item.createdAt ? dateTime(item.createdAt) : '처리 대기' }}</span>
              </div>

              <div class="requester-row">
                <span class="requester-avatar">{{ requester(item).name.charAt(0) }}</span>
                <div>
                  <strong>{{ requester(item).name }}</strong>
                  <span>{{ requester(item).email }}</span>
                </div>
                <span class="requester-role">{{ requester(item).role }}</span>
              </div>

              <p class="request-reason">{{ item.reason || item.course?.description || '검토할 요청입니다.' }}</p>

              <dl class="request-facts">
                <div>
                  <dt>카테고리</dt>
                  <dd>{{ categoryLabel(item.course?.category) }}</dd>
                </div>
                <div v-if="item.requestedFrom">
                  <dt>대여 기간</dt>
                  <dd>{{ item.requestedFrom }} → {{ item.dueDate }}</dd>
                </div>
                <div v-if="item.course?.availableQuantity != null">
                  <dt>현재 가용 재고</dt>
                  <dd :class="{ danger: Number(item.course.availableQuantity) <= 0 }">
                    {{ item.course.availableQuantity }}개
                  </dd>
                </div>
                <div v-if="item.course?.totalQuantity">
                  <dt>{{ tab === 'acquisition' || tab === 'intake' ? '요청 수량' : '전체 수량' }}</dt>
                  <dd>{{ item.course.totalQuantity }}개</dd>
                </div>
                <div v-if="item.course?.pickupLocation">
                  <dt>수령, 반납</dt>
                  <dd>{{ item.course.pickupLocation }}</dd>
                </div>
                <div v-if="item.amount != null">
                  <dt>예산 검토 금액</dt>
                  <dd>{{ money(item.amount) }}</dd>
                </div>
              </dl>

              <a
                v-if="item.course?.purchaseUrl && ['acquisition', 'budget', 'intake'].includes(tab)"
                :href="item.course.purchaseUrl"
                target="_blank"
                rel="noopener"
                class="reference-link"
              >
                구매 참고 링크 열기 ↗
              </a>

              <section v-if="tab === 'loan'" class="action-panel">
                <div v-if="Number(item.course?.availableQuantity) <= 0" class="stock-warning">
                  가용 재고가 없어 지금은 승인할 수 없습니다. 반납 확인 후 다시 처리해 주세요.
                </div>
                <label>
                  <span>반려 사유 <small>반려할 때만 필수</small></span>
                  <input v-model.trim="reviewComments[item.id]" placeholder="요청자에게 전달할 구체적인 사유" />
                </label>
                <div class="action-buttons">
                  <button class="btn btn-danger btn-sm" :disabled="busyKey === item.id" @click="askReject(item)">반려</button>
                  <button
                    class="btn btn-primary btn-sm"
                    :disabled="busyKey === item.id || Number(item.course?.availableQuantity) <= 0"
                    @click="askApproveLoan(item)"
                  >
                    대여 승인
                  </button>
                </div>
              </section>

              <section v-else-if="tab === 'return'" class="return-panel" :aria-busy="busyKey === item.id">
                <strong>반납 검수 체크리스트</strong>
                <p>실물 확인 후 세 항목을 모두 체크해야 재고를 복원할 수 있습니다.</p>
                <div class="return-checks">
                  <label
                    class="return-check"
                    :class="{ checked: returnChecks[item.id].condition, disabled: busyKey === item.id }"
                  >
                    <input v-model="returnChecks[item.id].condition" type="checkbox" :disabled="busyKey === item.id" />
                    <span class="return-check-indicator" aria-hidden="true"><AppIcon name="check" :size="14" /></span>
                    <span>외관, 작동 상태</span>
                  </label>
                  <label
                    class="return-check"
                    :class="{ checked: returnChecks[item.id].accessories, disabled: busyKey === item.id }"
                  >
                    <input v-model="returnChecks[item.id].accessories" type="checkbox" :disabled="busyKey === item.id" />
                    <span class="return-check-indicator" aria-hidden="true"><AppIcon name="check" :size="14" /></span>
                    <span>구성품, 충전기</span>
                  </label>
                  <label
                    class="return-check"
                    :class="{ checked: returnChecks[item.id].data, disabled: busyKey === item.id }"
                  >
                    <input v-model="returnChecks[item.id].data" type="checkbox" :disabled="busyKey === item.id" />
                    <span class="return-check-indicator" aria-hidden="true"><AppIcon name="check" :size="14" /></span>
                    <span>사용자 데이터 정리</span>
                  </label>
                </div>
                <button
                  class="btn btn-primary btn-sm"
                  :disabled="busyKey === item.id || !returnReady(item.id)"
                  @click="askConfirmReturn(item)"
                >
                  반납 확인, 재고 복원
                </button>
              </section>

              <section v-else-if="tab === 'acquisition'" class="action-panel">
                <label>
                  <span>반려 사유 <small>반려할 때만 필수</small></span>
                  <input v-model.trim="reviewComments[item.id]" placeholder="대체 장비나 보완할 근거를 함께 적어 주세요." />
                </label>
                <div class="action-buttons">
                  <button class="btn btn-danger btn-sm" :disabled="busyKey === item.id" @click="askReject(item)">반려</button>
                  <button class="btn btn-primary btn-sm" :disabled="busyKey === item.id" @click="askApproveAcquisition(item)">
                    필요성 승인
                  </button>
                </div>
              </section>

              <section v-else-if="tab === 'budget'" class="budget-panel">
                <div>
                  <small>학교 예산 검토</small>
                  <strong>{{ money(item.amount) }}</strong>
                </div>
                <div>
                  <button class="btn btn-danger btn-sm" :disabled="busyKey === item.paymentId" @click="askBudget(item, false)">
                    예산 반려
                  </button>
                  <button class="btn btn-primary btn-sm" :disabled="busyKey === item.paymentId" @click="askBudget(item, true)">
                    예산 승인
                  </button>
                </div>
              </section>

              <section v-else-if="tab === 'intake'" class="intake-panel">
                <div class="intake-fields">
                  <label>
                    <span>입고 수량</span>
                    <input v-model.number="intakeForms[item.id].receivedQuantity" type="number" min="1" />
                  </label>
                  <label>
                    <span>수령, 반납 장소</span>
                    <input v-model.trim="intakeForms[item.id].pickupLocation" placeholder="예: 공학관 301호" />
                  </label>
                  <label>
                    <span>대여 범위</span>
                    <select v-model="intakeForms[item.id].visibility">
                      <option value="GROUP">그룹 전용</option>
                      <option v-if="auth.isInstructor" value="ORGANIZATION">학교 공용</option>
                    </select>
                  </label>
                </div>
                <button class="btn btn-primary btn-sm" :disabled="busyKey === item.id" @click="askReceive(item)">
                  입고 완료, 자산 전환
                </button>
              </section>
            </article>
          </div>

          <div v-else class="empty-state surface">
            <span class="empty-icon" aria-hidden="true"><AppIcon name="check" :size="28" /></span>
            <strong>{{ keyword ? '검색 조건에 맞는 요청이 없습니다.' : '이 단계에서 처리할 요청이 없습니다.' }}</strong>
            <p>{{ keyword ? '검색어를 지우고 전체 대기열을 확인해 보세요.' : '워크플로 상태가 바뀌면 해당 탭에 자동으로 표시됩니다.' }}</p>
            <button v-if="keyword" class="btn btn-ghost" @click="keyword = ''">검색 초기화</button>
          </div>
        </template>

        <div v-else class="empty-state surface">
          <strong>그룹 관리자만 운영 데스크에 접근할 수 있습니다.</strong>
          <router-link :to="`/groups/${groupId}`" class="btn btn-outline">그룹 홈</router-link>
        </div>
      </div>
    </main>

    <ConfirmDialog
      :open="!!pendingAction"
      :title="pendingAction?.title || ''"
      :description="pendingAction?.description || ''"
      :confirm-label="pendingAction?.confirmLabel || '확인'"
      :tone="pendingAction?.tone || 'primary'"
      @cancel="pendingAction = null"
      @confirm="runPendingAction"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { courseApi } from '@/api/course.js'
import { enrollmentApi } from '@/api/enrollment.js'
import { groupApi } from '@/api/group.js'
import { paymentApi } from '@/api/payment.js'
import { useAuthStore } from '@/store/auth.js'
import { categoryLabel } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'
import { formatApiDateTime } from '@/utils/datetime.js'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupStore = useGroupStore()

const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const isManager = computed(() => auth.isInstructor || group.value?.currentRole === 'MANAGER')
const requestedTab = route.query.tab
const tab = ref(validTab(requestedTab) && (requestedTab !== 'budget' || auth.isInstructor)
  ? requestedTab
  : 'loan')
const loans = ref([])
const returns = ref([])
const acquisitions = ref([])
const budgets = ref([])
const intake = ref([])
const members = ref([])
const loading = ref(true)
const busyKey = ref(null)
const message = ref('')
const error = ref('')
const keyword = ref('')
const pendingAction = ref(null)
const reviewComments = reactive({})
const intakeForms = reactive({})
const returnChecks = reactive({})

const tabs = computed(() => [
  { key: 'loan', label: '대여 승인', count: loans.value.length },
  { key: 'return', label: '반납 확인', count: returns.value.length },
  { key: 'acquisition', label: '도입 검토', count: acquisitions.value.length },
  ...(auth.isInstructor ? [{ key: 'budget', label: '학교 예산', count: budgets.value.length }] : []),
  { key: 'intake', label: '입고', count: intake.value.length }
])
const currentItems = computed(() => ({
  loan: loans.value,
  return: returns.value,
  acquisition: acquisitions.value,
  budget: budgets.value,
  intake: intake.value
})[tab.value] || [])
const filteredItems = computed(() => {
  const needle = keyword.value.toLowerCase()
  if (!needle) return currentItems.value
  return currentItems.value.filter(item => {
    const person = requester(item)
    return `${item.course?.title || ''} ${item.reason || ''} ${person.name} ${person.email} ${requestNumber(item)}`
      .toLowerCase()
      .includes(needle)
  })
})
const tabLabel = computed(() => tabs.value.find(item => item.key === tab.value)?.label || '요청')

function validTab(value) {
  return ['loan', 'return', 'acquisition', 'budget', 'intake'].includes(value)
}

function setTab(value) {
  if (!validTab(value) || (value === 'budget' && !auth.isInstructor)) return
  tab.value = value
  keyword.value = ''
  router.replace({ query: { ...route.query, tab: value } })
}

const requestNumber = item => (
  item.paymentId
    ? `PAY-${String(item.paymentId).padStart(4, '0')}`
    : `REQ-${String(item.id).padStart(4, '0')}`
)
const money = value => `${Number(value || 0).toLocaleString()}원`
const dateTime = value => formatApiDateTime(value)
const explain = cause => (
  cause.response?.data?.message
  || cause.response?.data?.detail
  || cause.response?.data?.error
  || '요청을 처리하지 못했습니다.'
)

function requester(item) {
  const member = members.value.find(row => Number(row.userId) === Number(item.userId))
  return {
    name: member?.name || `사용자 ${item.userId || '-'}`,
    email: member?.email || '사용자 정보 없음',
    role: member?.groupRole === 'MANAGER' ? '그룹 관리자' : '구성원'
  }
}

function returnReady(id) {
  const checks = returnChecks[id]
  return !!checks?.condition && !!checks?.accessories && !!checks?.data
}

async function groupRequests(type, status) {
  const response = await enrollmentApi.getGroupRequests(groupId.value, type, status)
  return response.data?.data ?? []
}

async function attachCourses(payments) {
  return Promise.all(payments.map(async payment => {
    try {
      const response = await courseApi.getById(payment.courseId)
      return { ...payment, course: response.data?.data ?? response.data }
    } catch {
      return payment
    }
  }))
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    await groupStore.loadGroup(groupId.value)
    if (!isManager.value) return

    const tasks = [
      groupRequests('LOAN', 'PENDING'),
      groupRequests('LOAN', 'RETURN_REQUESTED'),
      groupRequests('PURCHASE', 'PENDING'),
      groupRequests('PURCHASE', 'BUDGET_APPROVED'),
      groupApi.getMembers(groupId.value)
    ]
    const [loanRows, returnRows, acquisitionRows, intakeRows, memberResponse] = await Promise.all(tasks)
    loans.value = loanRows
    returns.value = returnRows
    acquisitions.value = acquisitionRows
    intake.value = intakeRows
    members.value = memberResponse.data?.data ?? []

    for (const item of returnRows) {
      returnChecks[item.id] ??= { condition: false, accessories: false, data: false }
    }
    for (const item of intakeRows) {
      intakeForms[item.id] ??= {
        receivedQuantity: item.course?.totalQuantity || 1,
        pickupLocation: item.course?.pickupLocation || '',
        visibility: 'GROUP'
      }
    }

    if (auth.isInstructor) {
      const response = await paymentApi.getPending(groupId.value)
      budgets.value = await attachCourses(response.data?.data ?? [])
    } else {
      budgets.value = []
    }
  } catch (cause) {
    error.value = explain(cause)
  } finally {
    loading.value = false
  }
}

async function act(key, action, success) {
  busyKey.value = key
  error.value = ''
  message.value = ''
  try {
    await action()
    message.value = success
    await loadAll()
  } catch (cause) {
    error.value = explain(cause)
  } finally {
    busyKey.value = null
  }
}

function ask(config) {
  pendingAction.value = config
}

async function runPendingAction() {
  const action = pendingAction.value
  pendingAction.value = null
  if (action?.run) await action.run()
}

function askApproveLoan(item) {
  ask({
    title: `${item.course?.title} 대여를 승인할까요?`,
    description: `승인 즉시 가용 재고 1개가 배정됩니다. 대여 기간은 ${item.requestedFrom}부터 ${item.dueDate}까지입니다.`,
    confirmLabel: '대여 승인',
    run: () => act(item.id, () => enrollmentApi.approve(item.id), `${item.course?.title} 대여를 승인했습니다.`)
  })
}

function askApproveAcquisition(item) {
  ask({
    title: `${item.course?.title} 도입 필요성을 승인할까요?`,
    description: '승인하면 학교 예산 검토 단계로 이동합니다. 요청 사유와 예상 수량을 확인해 주세요.',
    confirmLabel: '필요성 승인',
    run: () => act(item.id, () => enrollmentApi.approveAcquisition(item.id), `${item.course?.title} 도입 필요성을 승인했습니다.`)
  })
}

function askReject(item) {
  if (!reviewComments[item.id]) {
    error.value = '반려 사유를 입력해 주세요.'
    return
  }
  ask({
    title: `${item.course?.title} 요청을 반려할까요?`,
    description: `요청자에게 “${reviewComments[item.id]}” 사유가 전달됩니다.`,
    confirmLabel: '요청 반려',
    tone: 'danger',
    run: () => act(item.id, () => enrollmentApi.reject(item.id, reviewComments[item.id]), '요청을 반려했습니다.')
  })
}

function askConfirmReturn(item) {
  ask({
    title: `${item.course?.title} 반납을 완료할까요?`,
    description: '외관, 구성품과 데이터 정리를 확인했습니다. 완료하면 가용 재고 1개가 즉시 복원됩니다.',
    confirmLabel: '반납 완료, 재고 복원',
    run: () => act(item.id, () => enrollmentApi.confirmReturn(item.id), `${item.course?.title} 반납을 확인하고 재고를 복원했습니다.`)
  })
}

function askBudget(item, approved) {
  ask({
    title: approved ? '학교 예산을 승인할까요?' : '학교 예산을 반려할까요?',
    description: approved
      ? `${money(item.amount)} 예산을 승인하면 입고 대기 단계로 이동합니다.`
      : `${money(item.amount)} 예산 요청을 반려하고 도입 절차를 종료합니다.`,
    confirmLabel: approved ? '예산 승인' : '예산 반려',
    tone: approved ? 'primary' : 'danger',
    run: () => act(
      item.paymentId,
      () => approved ? paymentApi.approve(item.paymentId) : paymentApi.reject(item.paymentId),
      approved ? '학교 예산을 승인했습니다. 이벤트 처리 후 입고 탭에 표시됩니다.' : '학교 예산을 반려했습니다.'
    )
  })
}

function askReceive(item) {
  const form = intakeForms[item.id]
  if (!form?.pickupLocation || Number(form.receivedQuantity) < 1) {
    error.value = '입고 수량과 수령, 반납 장소를 확인해 주세요.'
    return
  }
  ask({
    title: `${item.course?.title}을 자산으로 전환할까요?`,
    description: `${form.receivedQuantity}개를 ${form.pickupLocation}에서 대여 가능한 상태로 등록합니다.`,
    confirmLabel: '입고 완료, 자산 전환',
    run: () => act(item.id, () => enrollmentApi.receive(item.id, form), `${item.course?.title}을 대여 가능한 자산으로 전환했습니다.`)
  })
}

onMounted(loadAll)
</script>

<style scoped>
.admin-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 11px;
  margin-bottom: 15px;
}
.admin-summary button {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 15px;
  color: var(--color-text-primary);
  text-align: left;
  background: rgba(255, 255, 255, .76);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(12px);
  transition: transform .2s ease, border-color .2s ease, background-color .2s ease, box-shadow .2s ease;
}
.admin-summary button:hover:not(:disabled) {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, .92);
  border-color: var(--color-border-hover);
}
.admin-summary button.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 12%, transparent);
}
.summary-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  font-weight: 800;
}
.green { color: var(--color-success); background: var(--color-success-light); }
.blue { color: var(--color-info); background: var(--color-info-light); }
.amber { color: var(--color-warning); background: var(--color-warning-light); }
.purple { color: var(--color-ai); background: var(--color-ai-light); }
.admin-summary div { display: flex; flex-direction: column; }
.admin-summary small { color: var(--color-text-muted); font-size: 10px; }
.admin-summary strong { color: var(--color-navy); font-size: 22px; line-height: 1.2; }
.feedback { margin-bottom: 14px; }
.queue-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding: 10px;
  background: rgba(255, 255, 255, .78);
  backdrop-filter: blur(12px);
}
.tabs {
  display: flex;
  gap: 5px;
  overflow-x: auto;
}
.tabs button {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 8px 12px;
  color: var(--color-text-secondary);
  background: transparent;
  border: 0;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
  transition: color .18s ease, background-color .18s ease, box-shadow .18s ease;
}
.tabs button.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-primary) 22%, transparent);
}
.tabs span { opacity: .75; }
.queue-search {
  position: relative;
  min-width: 280px;
}
.queue-search-icon {
  position: absolute;
  top: 50%;
  left: 11px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  pointer-events: none;
  transform: translateY(-50%);
}
.queue-search input {
  width: 100%;
  height: 38px;
  padding: 0 11px 0 34px;
  color: var(--color-text-primary);
  background: rgba(247, 249, 252, .82);
  border: 1px solid var(--color-border);
  border-radius: 9px;
  font-size: 11px;
  outline: none;
  transition: background-color .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.queue-search input:focus-visible {
  background: rgba(255, 255, 255, .96);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 14%, transparent);
}
.approval-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
}
.approval-card {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 13px;
  padding: 20px;
  background: rgba(255, 255, 255, .78);
  backdrop-filter: blur(12px);
}
.request-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.request-type {
  color: var(--color-primary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .08em;
}
.request-header h2 {
  margin-top: 4px;
  color: var(--color-navy);
  font-size: 17px;
  line-height: 1.35;
}
.queue-age {
  color: var(--color-text-muted);
  font-size: 9px;
  white-space: nowrap;
}
.requester-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 10px;
  background: rgba(247, 249, 252, .76);
  border: 1px solid color-mix(in srgb, var(--color-border) 78%, transparent);
  border-radius: 10px;
}
.requester-avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-navy);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 800;
}
.requester-row > div {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.requester-row strong {
  overflow: hidden;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.requester-row div span {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.requester-role {
  padding: 4px 7px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 999px;
  font-size: 9px;
  font-weight: 750;
}
.request-reason {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.65;
}
.request-facts {
  display: flex;
  flex-wrap: wrap;
  gap: 9px 18px;
  margin: 0;
  padding: 0;
}
.request-facts div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.request-facts dt {
  color: var(--color-text-muted);
  font-size: 9px;
}
.request-facts dd {
  margin: 0;
  font-size: 10px;
  font-weight: 700;
}
.request-facts .danger { color: var(--color-danger); }
.reference-link {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 700;
}
.action-panel,
.return-panel,
.budget-panel,
.intake-panel {
  margin-top: auto;
  padding-top: 13px;
  border-top: 1px solid var(--color-border);
}
.action-panel label {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.action-panel label span {
  color: var(--color-text-secondary);
  font-size: 10px;
  font-weight: 700;
}
.action-panel label small {
  color: var(--color-text-muted);
  font-weight: 400;
}
.action-panel input,
.intake-panel input,
.intake-panel select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, .82);
  border: 1px solid var(--color-border);
  border-radius: 9px;
  outline: none;
  font-size: 10px;
  transition: background-color .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.action-panel input:focus-visible,
.intake-panel input:focus-visible,
.intake-panel select:focus-visible {
  background: #fff;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 14%, transparent);
}
.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 7px;
  margin-top: 8px;
}
.stock-warning {
  margin-bottom: 9px;
  padding: 9px 10px;
  color: var(--color-danger);
  background: var(--color-danger-light);
  border-radius: 8px;
  font-size: 10px;
}
.return-panel > strong { font-size: 11px; }
.return-panel > p {
  margin-top: 3px;
  color: var(--color-text-muted);
  font-size: 9px;
}
.return-checks {
  display: grid;
  gap: 7px;
  margin: 12px 0;
}
.return-check {
  position: relative;
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  min-height: 44px;
  padding: 8px 11px;
  color: var(--color-text-secondary);
  background: rgba(247, 249, 252, .72);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  font-size: 10px;
  font-weight: 700;
  transition: color .18s ease, background-color .18s ease, border-color .18s ease, transform .18s ease;
}
.return-check:hover:not(.disabled) {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, .94);
  border-color: var(--color-border-hover);
}
.return-check.checked {
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-color: color-mix(in srgb, var(--color-primary) 58%, var(--color-border));
}
.return-check.disabled {
  cursor: not-allowed;
  opacity: .58;
}
.return-check:has(input:focus-visible) {
  outline: 3px solid color-mix(in srgb, var(--color-primary) 18%, transparent);
  outline-offset: 2px;
}
.return-check input {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
.return-check-indicator {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  color: transparent;
  background: rgba(255, 255, 255, .88);
  border: 1px solid var(--color-border-hover);
  border-radius: 8px;
  transition: color .18s ease, background-color .18s ease, border-color .18s ease, transform .18s ease;
}
.return-check.checked .return-check-indicator {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
  transform: scale(1.03);
}
.return-panel > button { margin-left: auto; }
.empty-state .empty-icon {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  color: var(--color-success);
  background: color-mix(in srgb, var(--color-success-light) 76%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-success) 18%, transparent);
  border-radius: 15px;
}
.budget-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.budget-panel > div:first-child {
  display: flex;
  flex-direction: column;
}
.budget-panel small { color: var(--color-text-muted); font-size: 9px; }
.budget-panel strong { color: var(--color-navy); font-size: 17px; }
.budget-panel > div:last-child { display: flex; gap: 7px; }
.intake-panel {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 9px;
}
.intake-fields {
  width: 100%;
  display: grid;
  grid-template-columns: 85px 1fr 115px;
  gap: 7px;
}
.intake-fields label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.intake-fields span {
  color: var(--color-text-muted);
  font-size: 9px;
}

@media (max-width: 980px) {
  .approval-list { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .admin-summary { grid-template-columns: repeat(2, 1fr); }
  .queue-toolbar { align-items: stretch; flex-direction: column; }
  .queue-search { min-width: 0; }
}
@media (max-width: 560px) {
  .return-checks,
  .intake-fields { grid-template-columns: 1fr; }
  .budget-panel { align-items: flex-start; flex-direction: column; }
  .request-header { flex-direction: column; }
}
</style>
