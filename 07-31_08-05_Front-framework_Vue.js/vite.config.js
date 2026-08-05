import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // 개발 도구는 dev 서버에서만 포함하여 배포 번들의 크기와 경고를 줄인다.
  plugins: [vue(), command === 'serve' && vueDevTools()].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 🟢 [커스텀 추가 1] 로컬 개발 서버(Dev Server) 속성 제어
  server: {
    port: 3000, // 개발 서버의 네트워크 포트를 3000번으로 고정 명세
    open: true, // 프로세스 기동(npm run dev) 시 기본 웹 브라우저를 자동 실행
  },
  // 🟢 [커스텀 추가 2] 컴파일 완료된 산출물(Production Build) 사양 제어
  build: {
    outDir: 'dist', // 최종 정적 리소스(HTML, JS, CSS)가 저장될 출력 디렉토리명 지정
  },
  // [개인 추가 · GitHub Pages 배포] GitHub Pages에 "사용자명.github.io/저장소이름" 형태로 올릴 경우,
  // 루트(/)가 아니라 저장소 이름이 하위 경로가 되기 때문에 base를 반드시 저장소 이름으로 맞춰야
  // CSS/JS 파일 경로가 깨지지 않는다. 로컬 개발 중에는 필요 없어서 평소엔 주석으로 꺼둔다.
  // base: command === 'build' ? '/저장소-이름/' : '/',
}))
