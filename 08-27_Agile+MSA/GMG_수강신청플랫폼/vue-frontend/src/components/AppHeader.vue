<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link
        :to="auth.isAuthenticated ? '/groups' : '/'"
        class="brand"
        aria-label="Universal StoragE 홈"
      >
        <GearHubLogo />
      </router-link>

      <nav v-if="auth.isAuthenticated" class="desktop-nav" aria-label="주요 메뉴">
        <router-link to="/groups" class="nav-link">그룹</router-link>
        <template v-if="groupId">
          <router-link :to="groupPath('')" class="nav-link" exact-active-class="router-link-active">홈</router-link>
          <router-link :to="groupPath('/assets')" class="nav-link">자산 찾기</router-link>
          <router-link v-if="!isManager" :to="groupPath('/loans')" class="nav-link">내 요청</router-link>
          <router-link v-if="isManager" :to="groupPath('/admin')" class="nav-link">운영 데스크</router-link>
          <router-link v-if="isManager" :to="groupPath('/analytics')" class="nav-link ai-link"><AppIcon name="sparkle" :size="14" />AI 수요예측</router-link>
        </template>
      </nav>

      <div class="header-actions">
        <template v-if="auth.isAuthenticated">
          <select
            v-if="groups.length"
            :value="groupId || ''"
            class="group-select desktop-only"
            aria-label="그룹 전환"
            @change="changeGroup"
          >
            <option value="">그룹 선택</option>
            <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
          </select>

          <router-link to="/mypage" class="profile-link" aria-label="마이페이지">
            <span class="role-pill desktop-only">{{ roleLabel }}</span>
            <span class="avatar" aria-hidden="true"><AppIcon name="campus" :size="18" /></span>
          </router-link>

          <button
            class="logout-btn desktop-only"
            :disabled="loggingOut"
            @click="handleLogout"
          >
            {{ loggingOut ? '로그아웃 중' : '로그아웃' }}
          </button>

          <button
            class="mobile-menu-btn"
            type="button"
            :aria-expanded="mobileOpen"
            aria-controls="mobile-navigation"
            :aria-label="mobileOpen ? '메뉴 닫기' : '메뉴 열기'"
            @click="mobileOpen = !mobileOpen"
          >
            <span></span><span></span><span></span>
          </button>
        </template>
        <router-link v-else to="/login" class="btn btn-primary btn-sm">로그인</router-link>
      </div>
    </div>

    <transition name="mobile-menu">
      <div v-if="auth.isAuthenticated && mobileOpen" id="mobile-navigation" class="mobile-panel">
        <div class="mobile-panel-inner">
          <label v-if="groups.length" class="mobile-group-field">
            <span>현재 그룹</span>
            <select :value="groupId || ''" aria-label="모바일 그룹 전환" @change="changeGroup">
              <option value="">그룹 선택</option>
              <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
            </select>
          </label>

          <nav class="mobile-nav" aria-label="모바일 주요 메뉴">
            <router-link to="/groups">그룹 목록</router-link>
            <template v-if="groupId">
              <router-link :to="groupPath('')">그룹 홈</router-link>
              <router-link :to="groupPath('/assets')">자산 찾기</router-link>
              <router-link v-if="!isManager" :to="groupPath('/loans')">내 요청</router-link>
              <router-link v-if="isManager" :to="groupPath('/admin')">운영 데스크</router-link>
              <router-link v-if="isManager" :to="groupPath('/analytics')">AI 수요예측</router-link>
            </template>
            <router-link to="/mypage">마이페이지</router-link>
          </nav>

          <div class="mobile-account">
            <div>
              <strong>{{ auth.user?.name || '사용자' }}</strong>
              <span>{{ roleLabel }}, {{ auth.user?.email }}</span>
            </div>
            <button :disabled="loggingOut" @click="handleLogout">
              {{ loggingOut ? '처리 중' : '로그아웃' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </header>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import GearHubLogo from '@/components/GearHubLogo.vue'
import { useAuthStore } from '@/store/auth.js'
import { useGroupStore } from '@/store/group.js'

const auth = useAuthStore()
const groupStore = useGroupStore()
const route = useRoute()
const router = useRouter()
const mobileOpen = ref(false)
const loggingOut = ref(false)

const groupId = computed(() => Number(route.params.groupId) || null)
const groups = computed(() => groupStore.groups)
const isManager = computed(() => auth.isInstructor || groupStore.currentGroup?.currentRole === 'MANAGER')
const roleLabel = computed(() => (
  auth.isInstructor ? '학교 관리자' : (isManager.value ? '그룹 관리자' : '구성원')
))

const groupPath = suffix => `/groups/${groupId.value}${suffix}`

async function syncGroup(id) {
  if (!auth.isAuthenticated) return
  if (!groupStore.loaded) await groupStore.fetchGroups().catch(() => {})
  if (id) await groupStore.loadGroup(id).catch(() => {})
}

function changeGroup(event) {
  const id = Number(event.target.value)
  mobileOpen.value = false
  if (id) router.push(`/groups/${id}`)
  else router.push('/groups')
}

async function handleLogout() {
  if (loggingOut.value) return
  loggingOut.value = true
  groupStore.clear()
  await auth.logout(false, true)
  await router.replace('/')
  loggingOut.value = false
}

onMounted(() => syncGroup(groupId.value))
watch(groupId, id => syncGroup(id))
watch(() => route.fullPath, () => {
  mobileOpen.value = false
})
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, .96);
  border-bottom: 1px solid rgba(207, 220, 239, .92);
  backdrop-filter: blur(16px);
}
.header-inner {
  width: min(1220px, calc(100% - 36px));
  height: 70px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 22px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 9px;
  flex-shrink: 0;
}
.desktop-nav {
  display: flex;
  align-items: center;
  gap: 3px;
  flex: 1;
}
.nav-link {
  padding: 8px 10px;
  border-radius: 9px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}
.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.ai-link { display: inline-flex; align-items: center; gap: 5px; }
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 9px;
}
.group-select {
  max-width: 170px;
  height: 40px;
  padding: 0 30px 0 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 650;
}
.profile-link {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 3px 4px 3px 11px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: var(--transition);
}
.profile-link:hover { color: var(--color-primary); border-color: var(--color-border-hover); background: var(--color-primary-light); }
.role-pill {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 750;
}
.avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 9px;
  font-size: 12px;
  font-weight: 800;
}
.logout-btn {
  padding: 8px 4px;
  color: var(--color-text-muted);
  background: transparent;
  border: 0;
  font-size: 11px;
}
.logout-btn:hover {
  color: var(--color-danger);
}
.mobile-menu-btn {
  width: 40px;
  height: 40px;
  display: none;
  place-content: center;
  gap: 4px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 11px;
}
.mobile-menu-btn span {
  width: 18px;
  height: 2px;
  display: block;
  background: var(--color-navy);
  border-radius: 2px;
}
.mobile-panel {
  display: none;
  background: #fff;
  border-top: 1px solid var(--color-border);
  box-shadow: var(--shadow-md);
}
.mobile-panel-inner {
  width: min(100% - 28px, 560px);
  margin: 0 auto;
  padding: 16px 0 20px;
}
.mobile-group-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mobile-group-field span {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 700;
}
.mobile-group-field select {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 10px;
}
.mobile-nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  margin-top: 14px;
}
.mobile-nav a {
  padding: 11px 12px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  border-radius: 9px;
  font-size: 13px;
  font-weight: 650;
}
.mobile-nav a.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.mobile-account {
  margin-top: 14px;
  padding-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid var(--color-border);
}
.mobile-account div {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.mobile-account strong {
  font-size: 13px;
}
.mobile-account span {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mobile-account button {
  padding: 8px 11px;
  color: var(--color-danger);
  background: var(--color-danger-light);
  border: 0;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
}
.mobile-menu-enter-active,
.mobile-menu-leave-active {
  transition: opacity .18s ease, transform .18s ease;
}
.mobile-menu-enter-from,
.mobile-menu-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 940px) {
  .desktop-nav {
    overflow-x: auto;
  }
  .nav-link {
    padding-inline: 8px;
    font-size: 12px;
  }
  .role-pill {
    display: none;
  }
}

@media (max-width: 780px) {
  .header-inner {
    width: min(100% - 24px, 1220px);
    height: 64px;
  }
  .desktop-nav,
  .desktop-only {
    display: none;
  }
  .mobile-menu-btn,
  .mobile-panel {
    display: grid;
  }
  .mobile-panel {
    display: block;
  }
  .header-actions {
    gap: 7px;
  }
}

</style>
