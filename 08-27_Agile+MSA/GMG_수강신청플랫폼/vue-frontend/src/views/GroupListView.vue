<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <div class="page-heading">
          <div>
            <span class="eyebrow">CAMPUS WORKSPACES</span>
            <h1 class="page-title">내 그룹</h1>
          </div>
          <button class="btn btn-ghost" :disabled="loading" @click="load"><AppIcon name="refresh" :size="16" /> 새로고침</button>
        </div>

        <section v-if="!loading" class="group-summary" aria-label="그룹 현황">
          <div class="summary-card surface">
            <span class="summary-label">소속 그룹</span>
            <strong class="summary-value">{{ groups.length }}</strong>
            <small>참여 중인 워크스페이스</small>
          </div>
          <div class="summary-card surface">
            <span class="summary-label">관리 권한</span>
            <strong class="summary-value">{{ managerCount }}</strong>
          </div>
          <div class="summary-card surface">
            <span class="summary-label">구성원 권한</span>
            <strong class="summary-value">{{ memberCount }}</strong>
          </div>
        </section>

        <div class="group-layout">
          <section class="workspace-list" aria-labelledby="workspace-heading">
            <h2 id="workspace-heading" class="sr-only">워크스페이스 목록</h2>
            <div class="workspace-toolbar surface">
              <label class="search-field">
                <span class="sr-only">그룹 검색</span>
                <b aria-hidden="true"><AppIcon name="search" :size="18" /></b>
                <input v-model.trim="keyword" type="search" placeholder="그룹 이름이나 설명 검색" aria-label="그룹 검색" />
              </label>
              <div class="role-filter" role="group" aria-label="역할 필터">
                <button
                  v-for="item in roleFilters"
                  :key="item.value"
                  :class="{ active: roleFilter === item.value }"
                  :aria-pressed="roleFilter === item.value"
                  @click="roleFilter = item.value"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <div v-if="error" class="error-box list-feedback" role="alert">{{ error }}</div>

            <div v-if="loading" class="loading-state surface">
              <div class="spinner"></div>
              <span>소속 그룹을 불러오고 있습니다.</span>
            </div>

            <div v-else-if="filteredGroups.length" class="group-grid fade-in-up">
              <router-link
                v-for="(group, index) in filteredGroups"
                :key="group.id"
                :to="`/groups/${group.id}`"
                class="group-card surface"
              >
                <div class="group-card-top">
                  <div class="group-symbol" :class="`tone-${index % 4}`" aria-hidden="true"><AppIcon name="home" :size="22" /></div>
                  <span :class="['role', isManager(group) ? 'manager' : 'member']">
                    {{ isManager(group) ? '그룹 관리자' : '구성원' }}
                  </span>
                </div>
                <div class="group-copy">
                  <h2>{{ group.name }}</h2>
                  <p>{{ group.description || '그룹 장비와 대여 요청을 한곳에서 관리합니다.' }}</p>
                </div>
                <div class="group-card-bottom">
                  <span>{{ isManager(group) ? '운영 현황과 승인 업무 보기' : '대여 가능한 자산 보기' }}</span>
                  <b aria-hidden="true">→</b>
                </div>
              </router-link>
            </div>

            <div v-else class="empty-state surface">
              <span class="empty-icon" aria-hidden="true"><AppIcon name="home" :size="30" /></span>
              <strong>{{ groups.length ? '검색 조건에 맞는 그룹이 없습니다.' : '아직 참여한 그룹이 없습니다.' }}</strong>
              <p>{{ groups.length ? '검색어 또는 역할 필터를 바꿔 보세요.' : '운영자에게 받은 초대코드로 참여해 주세요.' }}</p>
              <button v-if="groups.length" class="btn btn-outline" @click="resetFilters">필터 초기화</button>
            </div>
          </section>

          <aside class="join-panel surface">
            <span class="panel-icon" aria-hidden="true"><AppIcon name="user" :size="23" /></span>
            <h2>초대코드로 참여</h2>
            <p>그룹 관리자에게 받은 코드를 입력하면 바로 워크스페이스에 참여합니다.</p>
            <form @submit.prevent="join">
              <label class="field">
                <span>초대코드</span>
                <input
                  v-model.trim="inviteCode"
                  class="form-input code-input"
                  maxlength="12"
                  placeholder="예: LAB2026A"
                  autocomplete="off"
                  @input="inviteCode = inviteCode.toUpperCase()"
                />
              </label>
              <button class="btn btn-primary btn-block" :disabled="busy || !inviteCode">
                {{ busyAction === 'join' ? '참여 중...' : '그룹 참여' }}
              </button>
            </form>

            <template v-if="auth.isInstructor">
              <div class="divider"><span>학교 관리자</span></div>
              <button class="btn btn-outline btn-block" :aria-expanded="showCreate" @click="toggleCreate">
                <AppIcon v-if="!showCreate" name="plus" :size="16" />{{ showCreate ? '그룹 생성 닫기' : '새 그룹 만들기' }}
              </button>
              <form v-if="showCreate" class="create-form" @submit.prevent="create">
                <label class="field">
                  <span>그룹 이름</span>
                  <input v-model.trim="newGroup.name" class="form-input" maxlength="80" placeholder="예: 로봇공학 연구실" />
                </label>
                <label class="field">
                  <span>그룹 설명 <small class="field-hint">선택</small></span>
                  <textarea v-model.trim="newGroup.description" class="form-textarea" maxlength="300" placeholder="운영 목적과 공유 장비를 설명해 주세요."></textarea>
                </label>
                <button class="btn btn-primary btn-block" :disabled="busy || newGroup.name.length < 2">
                  {{ busyAction === 'create' ? '생성 중...' : '그룹 생성' }}
                </button>
              </form>
            </template>

            <div v-if="panelError" class="error-box feedback" role="alert">{{ panelError }}</div>
            <div v-if="message" class="success-box feedback" role="status">{{ message }}</div>
          </aside>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import { groupApi } from '@/api/group.js'
import { useAuthStore } from '@/store/auth.js'
import { useGroupStore } from '@/store/group.js'

const auth = useAuthStore()
const groupStore = useGroupStore()
const router = useRouter()

const groups = computed(() => groupStore.groups)
const loading = computed(() => groupStore.loading)
const keyword = ref('')
const roleFilter = ref('ALL')
const inviteCode = ref('')
const showCreate = ref(false)
const busyAction = ref('')
const error = ref('')
const panelError = ref('')
const message = ref('')
const newGroup = reactive({ name: '', description: '' })

const roleFilters = [
  { value: 'ALL', label: '전체' },
  { value: 'MANAGER', label: '관리자' },
  { value: 'MEMBER', label: '구성원' }
]
const busy = computed(() => !!busyAction.value)
const managerCount = computed(() => groups.value.filter(isManager).length)
const memberCount = computed(() => groups.value.length - managerCount.value)
const filteredGroups = computed(() => {
  const needle = keyword.value.toLowerCase()
  return groups.value.filter(group => {
    const roleMatches = roleFilter.value === 'ALL'
      || (roleFilter.value === 'MANAGER' && isManager(group))
      || (roleFilter.value === 'MEMBER' && !isManager(group))
    const keywordMatches = !needle || `${group.name} ${group.description || ''}`.toLowerCase().includes(needle)
    return roleMatches && keywordMatches
  })
})

const isManager = group => auth.isInstructor || group.currentRole === 'MANAGER'
const explain = cause => cause.response?.data?.message
  || cause.response?.data?.detail
  || cause.response?.data?.error
  || '요청을 처리하지 못했습니다.'

async function load() {
  error.value = ''
  try {
    await groupStore.fetchGroups()
  } catch (cause) {
    error.value = explain(cause)
  }
}

function resetFilters() {
  keyword.value = ''
  roleFilter.value = 'ALL'
}

function toggleCreate() {
  showCreate.value = !showCreate.value
  panelError.value = ''
  message.value = ''
}

async function join() {
  busyAction.value = 'join'
  panelError.value = ''
  message.value = ''
  try {
    const response = await groupApi.join(inviteCode.value)
    const joined = response.data?.data ?? response.data
    await groupStore.fetchGroups()
    message.value = `${joined.name}에 참여했습니다.`
    inviteCode.value = ''
    router.push(`/groups/${joined.id}`)
  } catch (cause) {
    panelError.value = explain(cause)
  } finally {
    busyAction.value = ''
  }
}

async function create() {
  if (newGroup.name.length < 2) {
    panelError.value = '그룹 이름을 2자 이상 입력해 주세요.'
    return
  }
  busyAction.value = 'create'
  panelError.value = ''
  message.value = ''
  try {
    const response = await groupApi.create(newGroup)
    const created = response.data?.data ?? response.data
    await groupStore.fetchGroups()
    router.push(`/groups/${created.id}`)
  } catch (cause) {
    panelError.value = explain(cause)
  } finally {
    busyAction.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.group-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.group-summary small { margin-top: 2px; color: var(--color-text-muted); font-size: 10px; }
.group-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 22px;
  align-items: start;
}
.workspace-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding: 11px 12px;
}
.search-field { position: relative; flex: 1; max-width: 390px; }
.search-field b {
  position: absolute;
  top: 50%;
  left: 12px;
  color: var(--color-text-muted);
  transform: translateY(-50%);
}
.search-field input {
  width: 100%;
  height: 40px;
  padding: 0 13px 0 34px;
  color: var(--color-text-primary);
  background: var(--color-bg-secondary);
  border: 1px solid transparent;
  border-radius: 10px;
  outline: none;
  font-size: 12px;
}
.search-field input:focus { background: #fff; border-color: var(--color-primary); }
.role-filter { display: flex; gap: 5px; }
.role-filter button {
  min-height: 36px;
  padding: 7px 11px;
  color: var(--color-text-secondary);
  background: transparent;
  border: 0;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
}
.role-filter button.active { color: #fff; background: var(--color-primary-dark); }
.list-feedback { margin-bottom: 14px; }
.group-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.group-card {
  min-width: 0;
  min-height: 196px;
  display: flex;
  flex-direction: column;
  padding: 20px;
  transition: var(--transition);
}
.group-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); border-color: var(--color-border-hover); }
.group-card-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.group-symbol {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 14px;
  font-size: 18px;
  font-weight: 800;
}
.tone-1 { background: #3b82f6; }
.tone-2 { background: #4f72b8; }
.tone-3 { background: #254f91; }
.role {
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 800;
}
.role.manager { color: var(--color-primary); background: var(--color-primary-light); }
.role.member { color: var(--color-info); background: var(--color-info-light); }
.group-copy { flex: 1; margin-top: 15px; }
.group-copy h2 { color: var(--color-navy); font-size: 17px; }
.group-copy p { margin-top: 5px; color: var(--color-text-secondary); font-size: 11px; line-height: 1.55; }
.group-card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 16px;
  padding-top: 13px;
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border);
  font-size: 10px;
}
.group-card-bottom b { color: var(--color-primary); font-size: 15px; }
.join-panel { position: sticky; top: 90px; padding: 24px; }
.panel-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 12px;
  font-weight: 800;
}
.join-panel h2 { margin-top: 14px; color: var(--color-navy); font-size: 17px; }
.join-panel > p { margin: 5px 0 17px; color: var(--color-text-secondary); font-size: 11px; line-height: 1.55; }
.join-panel form { display: flex; flex-direction: column; gap: 10px; }
.code-input { text-transform: uppercase; letter-spacing: .12em; }
.divider { display: flex; align-items: center; gap: 8px; margin: 21px 0 13px; color: var(--color-text-muted); font-size: 9px; }
.divider::before, .divider::after { content: ''; height: 1px; flex: 1; background: var(--color-border); }
.create-form { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-border); }
.create-form .form-textarea { min-height: 80px; }
.feedback { margin-top: 12px; }
.empty-state { min-height: 330px; }

@media (max-width: 900px) {
  .group-layout { grid-template-columns: 1fr; }
  .join-panel { position: static; }
}
@media (max-width: 720px) {
  .group-summary, .group-grid { grid-template-columns: 1fr; }
  .workspace-toolbar { align-items: stretch; flex-direction: column; }
  .search-field { max-width: none; }
}
</style>
