<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <div v-if="permissionNotice" class="notice permission-notice" role="status">
          관리자 전용 화면입니다. 현재 권한으로 사용할 수 있는 그룹 홈으로 이동했습니다.
        </div>

        <div v-if="loading" class="loading-state surface">
          <div class="spinner"></div>
          <span>그룹 현황과 처리할 업무를 준비하고 있습니다.</span>
        </div>

        <template v-else-if="group">
          <section class="workspace-hero surface fade-in-up">
            <div class="hero-copy">
              <span class="eyebrow">{{ isManager ? 'GROUP OPERATIONS' : 'GROUP WORKSPACE' }}</span>
              <h1>{{ group.name }}</h1>
              <p>{{ group.description || '우리 그룹의 공용 장비를 함께 운영합니다.' }}</p>
              <div v-if="!isManager" class="hero-role">
                <span>구성원 모드</span>
                <small>자산을 찾고 내 요청을 추적합니다.</small>
              </div>
            </div>
            <div v-if="isManager" class="invite">
              <small>구성원 초대코드</small>
              <button :aria-label="`초대코드 ${group.inviteCode} 복사`" @click="copyInvite">
                {{ copied ? '복사됨 ✓' : group.inviteCode }}
              </button>
              <span>눌러서 복사</span>
            </div>
            <router-link v-else :to="path('/assets')" class="hero-action">
              <span aria-hidden="true"><AppIcon name="search" :size="22" /></span>
              <div><small>바로 시작</small><strong>대여 가능한 자산 찾기</strong></div>
              <b aria-hidden="true">→</b>
            </router-link>
          </section>

          <section class="dashboard-summary" aria-label="그룹 현황">
            <div class="summary-card surface">
              <span class="summary-label">조회 가능한 자산</span>
              <strong class="summary-value">{{ assets.length }}</strong>
              <small>학교 공용 + 그룹 전용</small>
            </div>
            <div class="summary-card surface">
              <span class="summary-label">{{ isManager ? '그룹 대여 중' : '내 대여 중' }}</span>
              <strong class="summary-value">{{ activeLoans }}</strong>
              <small>반납 확인 대기 포함</small>
            </div>
            <div class="summary-card surface">
              <span class="summary-label">{{ isManager ? '처리할 요청' : '내 처리 대기' }}</span>
              <strong class="summary-value warning">{{ pendingRequests }}</strong>
              <small>{{ isManager ? '승인, 반납, 도입' : '승인, 예산 검토 중' }}</small>
            </div>
            <div class="summary-card surface">
              <span class="summary-label">{{ isManager ? '그룹 구성원' : '대여 가능 자산' }}</span>
              <strong class="summary-value">{{ isManager ? (memberCount || '—') : availableCount }}</strong>
              <small>{{ isManager ? '활성 구성원' : '현재 재고 기준' }}</small>
            </div>
          </section>

          <section class="action-center surface">
            <div class="section-head">
              <div>
                <span class="eyebrow">{{ isManager ? 'TODAY\'S QUEUE' : 'NEXT ACTION' }}</span>
                <h2>{{ isManager ? '지금 처리할 업무' : '내 요청에서 이어서 할 일' }}</h2>
              </div>
              <router-link :to="isManager ? path('/admin') : path('/loans')">
                전체 보기 →
              </router-link>
            </div>

            <div v-if="actionItems.length" class="action-list">
              <router-link
                v-for="item in actionItems"
                :key="item.key"
                :to="item.to"
                class="action-row"
              >
                <span :class="['action-icon', item.tone]" aria-hidden="true"><AppIcon :name="item.icon" :size="20" /></span>
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.description }}</p>
                </div>
                <span class="action-count">{{ item.count }}</span>
                <b aria-hidden="true">→</b>
              </router-link>
            </div>
            <div v-else class="all-clear">
              <span aria-hidden="true"><AppIcon name="check" :size="22" /></span>
              <div>
                <strong>{{ isManager ? '처리 대기 업무가 없습니다.' : '진행 중인 요청이 없습니다.' }}</strong>
                <p>{{ isManager ? '새 요청이 들어오면 이곳에 우선순위대로 표시됩니다.' : '필요한 자산을 찾아 대여를 신청해 보세요.' }}</p>
              </div>
              <router-link :to="path('/assets')" class="btn btn-outline btn-sm">자산 찾기</router-link>
            </div>
          </section>

          <section class="module-grid">
            <router-link :to="path('/assets')" class="module surface">
              <span class="module-icon green"><AppIcon name="grid" :size="23" /></span>
              <div><strong>자산 카탈로그</strong><p>재고와 대여 조건을 비교합니다.</p></div>
              <b aria-hidden="true">→</b>
            </router-link>
            <router-link v-if="!isManager" :to="path('/loans')" class="module surface">
              <span class="module-icon blue"><AppIcon name="swap" :size="23" /></span>
              <div><strong>내 대여, 도입 요청</strong><p>승인과 반납 상태를 추적합니다.</p></div>
              <b aria-hidden="true">→</b>
            </router-link>
            <router-link v-if="!isManager" :to="path('/acquisitions/new')" class="module surface">
              <span class="module-icon amber"><AppIcon name="plus" :size="23" /></span>
              <div><strong>미보유 장비 요청</strong><p>필요성과 예상 비용을 제출합니다.</p></div>
              <b aria-hidden="true">→</b>
            </router-link>
            <router-link v-if="isManager" :to="path('/admin')" class="module surface">
              <span class="module-icon purple"><AppIcon name="check" :size="23" /></span>
              <div><strong>운영 데스크</strong><p>대여, 반납, 도입, 입고를 처리합니다.</p></div>
              <b aria-hidden="true">→</b>
            </router-link>
            <router-link v-if="isManager" :to="path('/analytics')" class="module ai-module">
              <span class="module-icon dark"><AppIcon name="sparkle" :size="23" /></span>
              <div><strong>AI 수요예측</strong><p>4주 부족 재고와 이동 대안을 확인합니다.</p></div>
              <b aria-hidden="true">→</b>
            </router-link>
          </section>

          <section class="recent surface">
            <div class="section-head">
              <div>
                <span class="eyebrow">AVAILABLE NOW</span>
                <h2>지금 대여 가능한 장비</h2>
              </div>
              <router-link :to="path('/assets?available=1')">전체 보기 →</router-link>
            </div>
            <div class="asset-row">
              <router-link
                v-for="asset in availableAssets"
                :key="asset.id"
                :to="path(`/assets/${asset.id}`)"
                class="mini-asset"
              >
                <span aria-hidden="true"><AppIcon :name="categoryIcon(asset.category)" :size="21" /></span>
                <div>
                  <strong>{{ asset.title }}</strong>
                  <small>{{ asset.availableQuantity }}개, {{ asset.pickupLocation || '운영실' }}</small>
                </div>
                <b aria-hidden="true">→</b>
              </router-link>
              <p v-if="!availableAssets.length" class="muted">현재 대여 가능한 자산이 없습니다.</p>
            </div>
          </section>
        </template>

        <div v-else class="empty-state surface">
          <strong>그룹 정보를 불러오지 못했습니다.</strong>
          <router-link to="/groups" class="btn btn-outline">그룹 목록</router-link>
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
import { courseApi } from '@/api/course.js'
import { enrollmentApi } from '@/api/enrollment.js'
import { groupApi } from '@/api/group.js'
import { useAuthStore } from '@/store/auth.js'
import { categoryIcon } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'

const route = useRoute()
const auth = useAuthStore()
const groupStore = useGroupStore()

const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const assets = ref([])
const requests = ref([])
const memberCount = ref(0)
const loading = ref(true)
const copied = ref(false)
const operations = reactive({
  pendingLoans: [],
  activeLoans: [],
  returns: [],
  acquisitions: [],
  intake: []
})

const isManager = computed(() => auth.isInstructor || group.value?.currentRole === 'MANAGER')
const permissionNotice = computed(() => route.query.notice === 'manager-required')
const availableCount = computed(() => assets.value.filter(item => Number(item.availableQuantity) > 0).length)
const activeLoans = computed(() => (
  isManager.value
    ? operations.activeLoans.length + operations.returns.length
    : requests.value.filter(item => item.requestType === 'LOAN' && ['ACTIVE', 'RETURN_REQUESTED'].includes(item.status)).length
))
const pendingRequests = computed(() => (
  isManager.value
    ? operations.pendingLoans.length + operations.returns.length + operations.acquisitions.length + operations.intake.length
    : requests.value.filter(item => ['PENDING', 'GROUP_APPROVED', 'BUDGET_APPROVED'].includes(item.status)).length
))
const availableAssets = computed(() => assets.value.filter(item => Number(item.availableQuantity) > 0).slice(0, 4))

const actionItems = computed(() => {
  if (isManager.value) {
    return [
      {
        key: 'loan',
        title: '대여 승인',
        description: '요청 기간과 현재 재고를 확인합니다.',
        count: operations.pendingLoans.length,
        icon: 'swap',
        tone: 'green',
        to: path('/admin?tab=loan')
      },
      {
        key: 'return',
        title: '반납 확인',
        description: '장비와 구성품을 확인하고 재고를 복원합니다.',
        count: operations.returns.length,
        icon: 'check',
        tone: 'blue',
        to: path('/admin?tab=return')
      },
      {
        key: 'acquisition',
        title: '도입, 입고 검토',
        description: '필요성과 예산 승인 장비를 검토합니다.',
        count: operations.acquisitions.length + operations.intake.length,
        icon: 'plus',
        tone: 'amber',
        to: path('/admin?tab=acquisition')
      }
    ].filter(item => item.count > 0)
  }

  const open = requests.value.filter(item => ['PENDING', 'GROUP_APPROVED', 'ACTIVE', 'RETURN_REQUESTED', 'BUDGET_APPROVED'].includes(item.status))
  return open.slice(0, 3).map(item => ({
    key: item.id,
    title: item.course?.title || `자산 #${item.courseId}`,
    description: ({
      PENDING: '관리자 검토를 기다리고 있습니다.',
      GROUP_APPROVED: '학교 예산 검토를 기다리고 있습니다.',
      ACTIVE: `${item.dueDate || '예정일'}까지 사용 후 반납해 주세요.`,
      RETURN_REQUESTED: '장비 전달 후 관리자 확인을 기다리고 있습니다.',
      BUDGET_APPROVED: '입고와 자산 전환을 기다리고 있습니다.'
    })[item.status],
    count: item.status === 'ACTIVE' ? '대여 중' : '진행 중',
    icon: item.status === 'ACTIVE' ? 'swap' : 'info',
    tone: item.status === 'ACTIVE' ? 'green' : 'amber',
    to: path('/loans')
  }))
})

const path = suffix => `/groups/${groupId.value}${suffix}`

async function copyInvite() {
  try {
    await navigator.clipboard.writeText(group.value.inviteCode)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1400)
  } catch {
    copied.value = false
  }
}

async function groupRequests(type, status) {
  const response = await enrollmentApi.getGroupRequests(groupId.value, type, status)
  return response.data?.data ?? []
}

async function loadManagerData() {
  const [members, pendingLoans, activeRows, returns, acquisitions, intake] = await Promise.all([
    groupApi.getMembers(groupId.value),
    groupRequests('LOAN', 'PENDING'),
    groupRequests('LOAN', 'ACTIVE'),
    groupRequests('LOAN', 'RETURN_REQUESTED'),
    groupRequests('PURCHASE', 'PENDING'),
    groupRequests('PURCHASE', 'BUDGET_APPROVED')
  ])
  memberCount.value = (members.data?.data ?? []).length
  operations.pendingLoans = pendingLoans
  operations.activeLoans = activeRows
  operations.returns = returns
  operations.acquisitions = acquisitions
  operations.intake = intake
}

async function load() {
  loading.value = true
  try {
    await groupStore.loadGroup(groupId.value)
    const [assetResponse, requestResponse] = await Promise.all([
      courseApi.getAll({ groupId: groupId.value }),
      enrollmentApi.getMyEnrollments(groupId.value)
    ])
    assets.value = assetResponse.data?.data ?? []
    requests.value = requestResponse.data?.data ?? []
    if (isManager.value) await loadManagerData()
  } finally {
    loading.value = false
  }
}

watch(groupId, load)
onMounted(load)
</script>

<style scoped>
.permission-notice { margin-bottom: 14px; }
.workspace-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 30px;
  margin-bottom: 16px;
  background: linear-gradient(125deg, #fff 52%, #eaf2ff);
}
.hero-copy h1 {
  color: var(--color-navy);
  font-size: 32px;
  letter-spacing: -.04em;
}
.hero-copy > p {
  margin-top: 7px;
  color: var(--color-text-secondary);
  font-size: 13px;
}
.hero-role {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}
.hero-role span {
  padding: 5px 8px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}
.hero-role small {
  color: var(--color-text-muted);
  font-size: 10px;
}
.invite {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.invite small,
.invite span {
  color: var(--color-text-muted);
  font-size: 9px;
}
.invite button {
  margin: 5px 0 3px;
  padding: 9px 14px;
  color: var(--color-primary);
  background: #fff;
  border: 1px dashed #8eb4ea;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .1em;
}
.hero-action {
  min-width: 255px;
  display: grid;
  grid-template-columns: 42px 1fr auto;
  align-items: center;
  gap: 11px;
  padding: 14px;
  background: rgba(255, 255, 255, .78);
  border: 1px solid var(--color-border);
  border-radius: 13px;
  box-shadow: var(--shadow-sm);
}
.hero-action > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 11px;
  font-size: 20px;
}
.hero-action div { display: flex; flex-direction: column; }
.hero-action small { color: var(--color-text-muted); font-size: 9px; }
.hero-action strong { color: var(--color-navy); font-size: 12px; }
.hero-action b { color: var(--color-primary); }
.dashboard-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.summary-card small {
  display: block;
  margin-top: 3px;
  color: var(--color-text-muted);
  font-size: 10px;
}
.summary-value.warning { color: var(--color-warning); }
.action-center {
  margin-top: 16px;
  padding: 22px;
}
.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
}
.section-head h2 {
  color: var(--color-navy);
  font-size: 19px;
}
.section-head > a {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}
.action-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 9px;
  margin-top: 15px;
}
.action-row {
  min-width: 0;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 10px;
  padding: 13px;
  background: var(--color-bg-secondary);
  border-radius: 11px;
}
.action-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  font-weight: 800;
}
.action-row > div { min-width: 0; }
.action-row strong {
  display: block;
  overflow: hidden;
  color: var(--color-navy);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.action-row p {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 9px;
  line-height: 1.5;
}
.action-count {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}
.action-row > b { color: var(--color-primary); }
.all-clear {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 15px;
  padding: 14px;
  background: var(--color-success-light);
  border-radius: 11px;
}
.all-clear > span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-success);
  border-radius: 11px;
  font-weight: 800;
}
.all-clear div { flex: 1; }
.all-clear strong { font-size: 12px; }
.all-clear p { color: var(--color-text-secondary); font-size: 10px; }
.module-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 13px;
  margin: 16px 0;
}
.module,
.ai-module {
  display: grid;
  grid-template-columns: 44px 1fr auto;
  align-items: center;
  gap: 13px;
  padding: 19px;
  transition: var(--transition);
}
.module:hover,
.ai-module:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.module-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  font-size: 18px;
}
.green { color: var(--color-success); background: var(--color-success-light); }
.blue { color: var(--color-info); background: var(--color-info-light); }
.amber { color: var(--color-warning); background: var(--color-warning-light); }
.purple { color: var(--color-primary-dark); background: var(--color-primary-light); }
.dark { color: var(--color-navy); background: #e7effb; }
.module strong { color: var(--color-navy); font-size: 13px; }
.module p { margin-top: 3px; color: var(--color-text-muted); font-size: 10px; }
.module b { color: var(--color-primary); }
.ai-module {
  color: var(--color-text-primary);
  background: linear-gradient(130deg, rgba(234, 242, 255, .96), rgba(247, 250, 255, .94));
  border: 1px solid #d2e1f5;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.ai-module strong { color: var(--color-text-primary); }
.ai-module p { color: var(--color-text-secondary); font-size: 10px; }
.ai-module b { color: var(--color-ai); }
.recent { padding: 22px; }
.asset-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 9px;
  margin-top: 15px;
}
.mini-asset {
  min-width: 0;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 10px;
}
.mini-asset > span {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: #fff;
  border-radius: 9px;
}
.mini-asset div {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.mini-asset strong {
  overflow: hidden;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mini-asset small { color: var(--color-text-muted); font-size: 9px; }
.mini-asset b { color: var(--color-primary); }
.muted { color: var(--color-text-muted); font-size: 11px; }

@media (max-width: 980px) {
  .dashboard-summary { grid-template-columns: repeat(2, 1fr); }
  .action-list { grid-template-columns: 1fr; }
  .module-grid { grid-template-columns: repeat(2, 1fr); }
  .asset-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 650px) {
  .workspace-hero { align-items: flex-start; flex-direction: column; }
  .invite { align-items: flex-start; }
  .hero-action { width: 100%; min-width: 0; }
  .module-grid,
  .asset-row { grid-template-columns: 1fr; }
  .all-clear { align-items: flex-start; flex-wrap: wrap; }
}
</style>
