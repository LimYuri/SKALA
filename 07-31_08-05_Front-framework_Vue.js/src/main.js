// 전역 CSS
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 사용하는 컴포넌트만 선택 import (번들 용량 절감)
import { Button, Empty, Switch, Tag } from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import router from './router'

const app = createApp(App).use(createPinia()).use(router)

// Ant Design Vue 컴포넌트 등록
const antComponents = [Button, Empty, Switch, Tag]
antComponents.forEach((component) => app.use(component))

app.mount('#app')
