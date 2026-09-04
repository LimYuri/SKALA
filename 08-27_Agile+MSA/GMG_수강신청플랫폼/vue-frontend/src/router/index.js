import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth.js'
import { useGroupStore } from '@/store/group.js'

function legacyGroupPath(suffix = '') {
  const groupId = sessionStorage.getItem('current_group_id')
  return groupId ? `/groups/${groupId}${suffix}` : '/groups'
}

const routes = [
  { path: '/', name: 'Landing', component: () => import('@/views/LandingView.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { guestOnly: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { guestOnly: true } },
  { path: '/callback', name: 'Callback', component: () => import('@/views/CallbackView.vue') },
  { path: '/groups', name: 'GroupList', component: () => import('@/views/GroupListView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)', name: 'GroupDashboard', component: () => import('@/views/GroupDashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)/assets', name: 'CourseList', component: () => import('@/views/CourseListView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)/assets/new', name: 'CourseCreate', component: () => import('@/views/CourseCreateView.vue'), meta: { requiresAuth: true, managerOnly: true } },
  { path: '/groups/:groupId(\\d+)/assets/:id(\\d+)', name: 'CourseDetail', component: () => import('@/views/CourseDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)/loans', name: 'Enrollment', component: () => import('@/views/EnrollmentView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)/acquisitions/new', name: 'PurchaseRequest', component: () => import('@/views/PurchaseRequestView.vue'), meta: { requiresAuth: true } },
  { path: '/groups/:groupId(\\d+)/admin', name: 'AdminApproval', component: () => import('@/views/AdminApprovalView.vue'), meta: { requiresAuth: true, managerOnly: true } },
  { path: '/groups/:groupId(\\d+)/analytics', name: 'Analytics', component: () => import('@/views/AnalyticsView.vue'), meta: { requiresAuth: true, managerOnly: true } },
  { path: '/mypage', name: 'MyPage', component: () => import('@/views/MyPageView.vue'), meta: { requiresAuth: true } },

  // 기존 실습 URL을 북마크한 경우 현재 그룹 워크스페이스로 안내한다.
  { path: '/courses', redirect: () => legacyGroupPath('/assets') },
  { path: '/courses/new', redirect: () => legacyGroupPath('/assets/new') },
  { path: '/courses/:id(\\d+)', redirect: to => legacyGroupPath(`/assets/${to.params.id}`) },
  { path: '/enrollments', redirect: () => legacyGroupPath('/loans') },
  { path: '/requests/new', redirect: () => legacyGroupPath('/acquisitions/new') },
  { path: '/admin/approvals', redirect: () => legacyGroupPath('/admin') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'Login', query: { redirect: to.fullPath } }
  if (to.meta.guestOnly && auth.isAuthenticated) return { name: 'GroupList' }
  if (to.meta.managerOnly && auth.user?.role !== 'INSTRUCTOR') {
    const groupId = Number(to.params.groupId)
    const groupStore = useGroupStore()
    try {
      const group = await groupStore.loadGroup(groupId)
      if (group?.currentRole !== 'MANAGER') {
        return {
          name: 'GroupDashboard',
          params: { groupId },
          query: { notice: 'manager-required' }
        }
      }
    } catch {
      return { name: 'GroupList' }
    }
  }
})

export default router
