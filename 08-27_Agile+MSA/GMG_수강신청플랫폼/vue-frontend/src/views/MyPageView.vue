<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container profile-layout">
        <aside class="profile-card surface">
          <div class="large-avatar" aria-hidden="true"><AppIcon name="campus" :size="32" /></div>
          <span class="role-badge">{{ auth.isInstructor ? '학교 관리자' : '학교 구성원' }}</span>
          <h2>{{ auth.user?.name || '사용자' }}</h2>
          <p>{{ auth.user?.email }}</p>

          <dl class="account-facts">
            <div>
              <dt>계정 역할</dt>
              <dd>{{ auth.isInstructor ? '전체 그룹 운영 가능' : '소속 그룹 이용' }}</dd>
            </div>
            <div>
              <dt>현재 워크스페이스</dt>
              <dd>{{ currentGroup?.name || '선택 전' }}</dd>
            </div>
          </dl>

          <div class="profile-note">
            <span aria-hidden="true"><AppIcon name="info" :size="16" /></span>
            <p>도입 요청의 금액은 예산 검토용이며 서비스 안에서 실제 결제가 발생하지 않습니다.</p>
          </div>
        </aside>

        <section class="profile-content">
          <div class="page-heading compact-heading">
            <div>
              <h1 class="page-title">나의 캠퍼스 허브</h1>
              <p class="page-subtitle">소속 그룹과 전체 요청 현황을 한눈에 확인하고, 최근 업무를 이어가세요.</p>
            </div>
            <button class="btn btn-ghost" :disabled="loading" @click="load"><AppIcon name="refresh" :size="16" /> 새로고침</button>
          </div>

          <div v-if="error" class="error-box page-feedback" role="alert">{{ error }}</div>

          <div v-if="loading" class="loading-state surface">
            <div class="spinner"></div>
            <span>계정 현황을 불러오고 있습니다.</span>
          </div>

          <template v-else>
            <section class="profile-summary" aria-label="내 이용 현황">
              <div class="summary-card surface">
                <span class="summary-label">소속 그룹</span>
                <strong class="summary-value">{{ groups.length }}</strong>
                <small>참여 중인 공간</small>
              </div>
              <div class="summary-card surface">
                <span class="summary-label">진행 중 요청</span>
                <strong class="summary-value">{{ openCount }}</strong>
                <small>검토, 대여, 입고 대기</small>
              </div>
              <div class="summary-card surface">
                <span class="summary-label">현재 대여</span>
                <strong class="summary-value">{{ activeCount }}</strong>
                <small>반납 확인 대기 포함</small>
              </div>
              <div class="summary-card surface">
                <span class="summary-label">완료 이력</span>
                <strong class="summary-value">{{ completedCount }}</strong>
                <small>반납, 입고 완료</small>
              </div>
            </section>

            <section v-if="!auth.isInstructor" class="quick-grid" aria-label="빠른 이동">
              <router-link to="/groups" class="quick-card surface">
                <span aria-hidden="true"><AppIcon name="home" :size="22" /></span>
                <div><strong>그룹 선택</strong><p>워크스페이스를 전환합니다.</p></div>
                <b aria-hidden="true">→</b>
              </router-link>
              <router-link v-if="currentId" :to="`/groups/${currentId}/assets`" class="quick-card surface">
                <span aria-hidden="true"><AppIcon name="search" :size="22" /></span>
                <div><strong>자산 찾기</strong><p>재고와 대여 조건을 비교합니다.</p></div>
                <b aria-hidden="true">→</b>
              </router-link>
              <router-link v-if="currentId" :to="`/groups/${currentId}/loans`" class="quick-card surface">
                <span aria-hidden="true"><AppIcon name="swap" :size="22" /></span>
                <div><strong>내 요청</strong><p>승인과 반납 상태를 확인합니다.</p></div>
                <b aria-hidden="true">→</b>
              </router-link>
            </section>

            <section class="recent-requests surface">
              <div class="section-head">
                <div>
                  <span class="eyebrow">RECENT ACTIVITY</span>
                  <h2>최근 요청</h2>
                </div>
                <router-link v-if="currentId" :to="`/groups/${currentId}/loans`">현재 그룹 요청 보기 →</router-link>
              </div>

              <div v-if="recentRequests.length" class="activity-list">
                <router-link
                  v-for="item in recentRequests"
                  :key="item.id"
                  :to="requestPath(item)"
                  class="activity-row"
                >
                  <span :class="['activity-icon', item.requestType === 'PURCHASE' ? 'purchase' : 'loan']" aria-hidden="true">
                    <AppIcon :name="item.requestType === 'PURCHASE' ? 'plus' : 'swap'" :size="19" />
                  </span>
                  <div class="activity-copy">
                    <div>
                      <StatusBadge :status="item.status" />
                      <span>REQ-{{ String(item.id).padStart(4, '0') }}</span>
                    </div>
                    <strong>{{ item.course?.title || `자산 #${item.courseId}` }}</strong>
                    <small>{{ groupName(item.groupId) }}, {{ dateTime(item.createdAt) }}</small>
                  </div>
                  <b aria-hidden="true">→</b>
                </router-link>
              </div>
              <div v-else class="inline-empty">
                <span aria-hidden="true"><AppIcon name="swap" :size="21" /></span>
                <div><strong>아직 요청 이력이 없습니다.</strong><p>그룹에서 필요한 자산을 찾아 첫 대여를 시작해 보세요.</p></div>
              </div>
            </section>

            <section class="groups surface">
              <div class="section-head">
                <div>
                  <span class="eyebrow">WORKSPACES</span>
                  <h2>내 그룹</h2>
                </div>
                <router-link to="/groups">전체 보기 →</router-link>
              </div>
              <div class="group-list">
                <router-link v-for="group in groups" :key="group.id" :to="`/groups/${group.id}`">
                  <span aria-hidden="true"><AppIcon name="home" :size="18" /></span>
                  <div>
                    <strong>{{ group.name }}</strong>
                    <small>{{ isManager(group) ? '그룹 관리자' : '구성원' }}</small>
                  </div>
                  <b aria-hidden="true">→</b>
                </router-link>
                <p v-if="!groups.length">참여 중인 그룹이 없습니다.</p>
              </div>
            </section>

          </template>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppHeader from '@/components/AppHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { enrollmentApi } from '@/api/enrollment.js'
import { useAuthStore } from '@/store/auth.js'
import { useGroupStore } from '@/store/group.js'
import { formatApiDateTime, parseApiDateTime } from '@/utils/datetime.js'
import { isOpenRequest } from '@/utils/requestStatus.js'

const auth = useAuthStore()
const groupStore = useGroupStore()
const requests = ref([])
const loading = ref(true)
const error = ref('')

const groups = computed(() => groupStore.groups)
const currentId = computed(() => {
  const selected = groupStore.currentGroup?.id || Number(sessionStorage.getItem('current_group_id'))
  return groups.value.some(group => group.id === selected) ? selected : groups.value[0]?.id || null
})
const currentGroup = computed(() => groups.value.find(group => group.id === currentId.value) || null)
const openCount = computed(() => requests.value.filter(item => isOpenRequest(item.status)).length)
const activeCount = computed(() => requests.value.filter(item => item.requestType === 'LOAN' && ['ACTIVE', 'RETURN_REQUESTED'].includes(item.status)).length)
const completedCount = computed(() => requests.value.filter(item => ['RETURNED', 'RECEIVED'].includes(item.status)).length)
const recentRequests = computed(() => [...requests.value]
  .sort((a, b) => (parseApiDateTime(b.createdAt)?.getTime() || 0) - (parseApiDateTime(a.createdAt)?.getTime() || 0))
  .slice(0, 5))

const isManager = group => auth.isInstructor || group.currentRole === 'MANAGER'
const groupName = id => groups.value.find(group => group.id === Number(id))?.name || '소속 그룹'
const dateTime = value => formatApiDateTime(value)
const requestPath = item => item.groupId || currentId.value
  ? `/groups/${item.groupId || currentId.value}/loans`
  : '/groups'

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [, response] = await Promise.all([
      groupStore.fetchGroups(),
      enrollmentApi.getMyEnrollments()
    ])
    requests.value = response.data?.data ?? []
  } catch (cause) {
    error.value = cause.response?.data?.message || '계정 현황을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.profile-layout { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 24px; align-items: start; }
.profile-card { position: sticky; top: 90px; padding: 28px; text-align: center; }
.large-avatar {
  width: 72px;
  height: 72px;
  margin: 0 auto 14px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border: 1px solid rgba(255, 255, 255, .35);
  border-radius: 20px;
  box-shadow: 0 12px 28px rgba(40, 70, 92, .14);
}
.role-badge {
  display: inline-flex;
  padding: 5px 9px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
}
.profile-card h2 { margin-top: 10px; color: var(--color-navy); font-size: 20px; }
.profile-card > p { margin-top: 3px; color: var(--color-text-muted); font-size: 11px; overflow-wrap: anywhere; }
.account-facts { display: grid; gap: 9px; margin-top: 22px; padding: 17px 0; border-block: 1px solid var(--color-border); }
.account-facts > div { display: flex; justify-content: space-between; gap: 12px; text-align: left; }
.account-facts dt { color: var(--color-text-muted); font-size: 10px; }
.account-facts dd { color: var(--color-navy); font-size: 10px; font-weight: 700; text-align: right; }
.profile-note { display: flex; align-items: flex-start; gap: 8px; margin-top: 17px; text-align: left; }
.profile-note > span {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  color: var(--color-info);
  background: var(--color-info-light);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 800;
}
.profile-note p { color: var(--color-text-muted); font-size: 9px; line-height: 1.6; }
.profile-content { min-width: 0; }
.compact-heading { margin-bottom: 22px; }
.page-feedback { margin-bottom: 14px; }
.profile-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 15px; }
.profile-summary small { margin-top: 2px; color: var(--color-text-muted); font-size: 9px; }
.quick-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.quick-card {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  padding: 17px;
  transition: var(--transition);
}
.quick-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--color-border-hover); }
.quick-card > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 11px;
  font-weight: 800;
}
.quick-card div { min-width: 0; display: flex; flex-direction: column; }
.quick-card strong { color: var(--color-navy); font-size: 12px; }
.quick-card p { color: var(--color-text-muted); font-size: 9px; }
.quick-card > b { color: var(--color-primary); }
.recent-requests, .groups { margin-top: 16px; padding: 21px; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; }
.section-head h2 { color: var(--color-navy); font-size: 17px; }
.section-head a { color: var(--color-primary); font-size: 10px; font-weight: 700; }
.activity-list { display: grid; margin-top: 14px; }
.activity-row {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  padding: 12px 4px;
  border-top: 1px solid var(--color-border);
}
.activity-row:first-child { border-top: 0; }
.activity-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 11px;
  font-weight: 800;
}
.activity-icon.purchase { color: var(--color-warning); background: var(--color-warning-light); }
.activity-copy { min-width: 0; }
.activity-copy > div { display: flex; align-items: center; gap: 7px; }
.activity-copy > div > span { color: var(--color-text-muted); font-size: 9px; }
.activity-copy > strong { display: block; margin-top: 5px; overflow: hidden; color: var(--color-navy); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.activity-copy > small { display: block; margin-top: 2px; color: var(--color-text-muted); font-size: 9px; }
.activity-row > b { color: var(--color-primary); }
.inline-empty { display: flex; align-items: center; gap: 12px; margin-top: 14px; padding: 20px; background: var(--color-bg-secondary); border-radius: 12px; }
.inline-empty > span { font-size: 22px; }
.inline-empty strong { color: var(--color-navy); font-size: 12px; }
.inline-empty p { margin-top: 2px; color: var(--color-text-muted); font-size: 10px; }
.group-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-top: 14px; }
.group-list > a {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 11px;
  background: var(--color-bg-secondary);
  border-radius: 10px;
}
.group-list > a > span {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 9px;
  font-size: 11px;
  font-weight: 800;
}
.group-list div { min-width: 0; display: flex; flex-direction: column; }
.group-list strong { overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.group-list small, .group-list > p { color: var(--color-text-muted); font-size: 9px; }
.group-list b { color: var(--color-primary); }

@media (max-width: 980px) {
  .profile-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .quick-grid { grid-template-columns: 1fr; }
}
@media (max-width: 850px) {
  .profile-layout { grid-template-columns: 1fr; }
  .profile-card { position: static; }
}
@media (max-width: 650px) {
  .profile-summary, .group-list { grid-template-columns: 1fr; }
}
</style>
