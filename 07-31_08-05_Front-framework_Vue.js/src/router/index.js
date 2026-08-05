import { createRouter, createWebHistory } from 'vue-router'

// 홈 화면은 즉시 로드
import WeatherExploreView from '@/views/WeatherExploreView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 오늘 날씨 목록 (홈)
    { path: '/', name: 'weather-explore', component: WeatherExploreView },
    {
      // 도시 상세 예보, 상세 정보는 query string으로 전달
      path: '/weather/:cityId',
      name: 'weather-detail',
      component: () => import('@/views/WeatherForecastView.vue'),
    },
    {
      // 두 도시 비교
      path: '/compare',
      name: 'weather-compare',
      component: () => import('@/views/WeatherCompareView.vue'),
    },
    {
      // 시/도-시/군/구 선택 또는 검색
      path: '/search',
      name: 'weather-search',
      component: () => import('@/views/SearchView.vue'),
    },
    {
      // 전국 지도 기온 한눈에 보기
      path: '/nationwide',
      name: 'weather-nationwide',
      component: () => import('@/views/NationwideWeatherView.vue'),
    },
    {
      // 병원·약국·관광정보 (생활 정보)
      path: '/nearby',
      name: 'nearby-info',
      component: () => import('@/views/NearbyInfoView.vue'),
    },
    {
      // 나머지 모든 경로 (404)
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
  // 페이지 이동 시 스크롤 위치 처리
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.path === from.path) return false
    return { top: 0 }
  },
})

export default router
