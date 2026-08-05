<script setup>
import { RouterLink, RouterView } from 'vue-router'
// Ant Design Vue 테마를 브랜드 색상으로 통일
import { ConfigProvider as AConfigProvider } from 'ant-design-vue'
const brandTheme = { token: { colorPrimary: '#2f8fe0', borderRadius: 10, fontFamily: 'Inter, Pretendard, "Noto Sans KR", sans-serif' } }

// 온도 단위 토글
import UnitToggler from '@/components/exercise/UnitToggler.vue'
// 라이트/다크 모드 토글
import ThemeToggler from '@/components/exercise/ThemeToggler.vue'
// 전역 토스트 알림
import ToastHost from '@/components/exercise/ToastHost.vue'

// 빌드 모드 표시 (dev/staging/production)
const appMode = import.meta.env.VITE_APP_MODE
console.log('현재 빌드 모드:', appMode)
</script>

<template>
  <!-- Ant Design Vue 컴포넌트 전체에 테마 적용 -->
  <a-config-provider :theme="brandTheme">
    <div class="app-shell">
      <header class="topbar">
        <nav aria-label="주요 메뉴">
          <RouterLink to="/">오늘날씨</RouterLink>
          <RouterLink to="/search">검색</RouterLink>
          <RouterLink to="/compare">지역 비교</RouterLink>
          <RouterLink to="/nationwide">전국 날씨</RouterLink>
          <RouterLink to="/nearby">생활 정보</RouterLink>
        </nav>
        <UnitToggler />
        <ThemeToggler />
      </header>
      <!-- 홈 화면은 KeepAlive로 캐싱해 뒤로가기 시 재요청 방지, 페이지 전환은 페이드 애니메이션 -->
      <RouterView v-slot="{ Component }">
        <KeepAlive include="WeatherExploreView">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </KeepAlive>
      </RouterView>
      <!-- 현재 빌드 모드 표시 -->
      <footer class="build-mode">{{ appMode }}</footer>
      <ToastHost />
    </div>
  </a-config-provider>
</template>
