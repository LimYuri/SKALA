<template>
  <div class="landing">
    <AppHeader />

    <main>
      <section class="hero">
        <div class="container hero-grid">
          <div class="hero-copy reveal is-visible">
            <h1><em>U</em>niversal <em>S</em>torag<em>E</em></h1>
            <p>워크스페이스를 만들고, 자산의 대여, 반납, 도입을 연결합니다.</p>
            <div class="hero-actions">
              <router-link :to="auth.isAuthenticated ? '/groups' : '/login'" class="btn btn-primary btn-lg">
                <template v-if="auth.isAuthenticated">내 그룹 들어가기</template>
                <span v-else class="brand-button-label"><em>U</em>niversal <em>S</em>torag<em>E</em> 시작하기</span>
              </router-link>
              <router-link v-if="auth.isAuthenticated" to="/groups" class="btn btn-outline btn-lg">그룹 선택</router-link>
            </div>
            <div class="trust-row">
              <span><AppIcon name="check" :size="13" />그룹별 권한</span><span><AppIcon name="check" :size="13" />대여, 반납 추적</span><span><AppIcon name="check" :size="13" />AI 수요예측</span>
            </div>
          </div>

          <div class="workflow-card reveal is-visible reveal-delay-1">
            <div class="workflow-head">
              <div><strong>조직 자산 운영 현황</strong></div>
              <span class="live-dot">운영 중</span>
            </div>
            <div class="workflow-list">
              <div v-for="(item, index) in workflow" :key="item.title" class="workflow-item" :style="{ '--delay': `${index * 70}ms` }">
                <span class="step">0{{ index + 1 }}</span>
                <span class="workflow-icon"><AppIcon :name="item.icon" :size="20" /></span>
                <div><strong>{{ item.title }}</strong><small>{{ item.desc }}</small></div>
                <span class="arrow">→</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section ref="categorySection" class="category-section reveal-section">
        <div class="container">
          <div class="section-heading">
            <div><span class="eyebrow">RESOURCE CATEGORIES</span><h2>편리한 업무, 교육 장비 관리</h2></div>
            <router-link :to="auth.isAuthenticated ? '/groups' : '/login'" class="text-link">그룹에서 자산 보기 →</router-link>
          </div>
          <div class="category-grid">
            <article v-for="(item, index) in categories" :key="item.title" class="category-card reveal-item" :style="{ '--item-delay': `${index * 80}ms` }">
              <span><AppIcon :name="item.icon" :size="23" /></span><div><h3>{{ item.title }}</h3><p>{{ item.desc }}</p></div>
            </article>
          </div>
        </div>
      </section>

      <section ref="whySection" class="why-section reveal-section">
        <div class="container why-grid">
          <div class="why-copy">
            <span class="eyebrow">WHY GEARHUB</span>
            <h2>AI와 함께 장비수요를 예측해보세요</h2>
            <p>18개월 요청 이력을 학습해 관리자에게 부족 재고와 그룹 간 이동 대안을 보여줍니다.</p>
          </div>
          <div class="benefit-list">
            <div v-for="(benefit, index) in benefits" :key="benefit.title" class="benefit reveal-item" :style="{ '--item-delay': `${index * 90}ms` }">
              <span>{{ benefit.number }}</span><div><strong>{{ benefit.title }}</strong><p>{{ benefit.desc }}</p></div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer><div class="container"><strong>Universal StoragE</strong></div></footer>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import { useAuthStore } from '@/store/auth.js'

const auth = useAuthStore()
const categorySection = ref(null)
const whySection = ref(null)
let revealObserver

onMounted(() => {
  revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return
      entry.target.classList.add('is-visible')
      revealObserver.unobserve(entry.target)
    })
  }, { threshold: 0.16 })
  ;[categorySection.value, whySection.value].filter(Boolean).forEach(section => revealObserver.observe(section))
})

onBeforeUnmount(() => revealObserver?.disconnect())
const workflow = [
  { icon: 'home', title: '그룹 워크스페이스', desc: '학과, 연구실, 동아리별 공간' },
  { icon: 'swap', title: '대여와 반납', desc: '기간, 승인, 재고를 함께 추적' },
  { icon: 'sparkle', title: '관리자 수요예측', desc: '4주 부족 수량과 이동 대안' }
]
const categories = [
  { icon: 'device', title: '스마트기기', desc: 'iPhone, Android, 태블릿' },
  { icon: 'computer', title: '컴퓨터', desc: '노트북, 워크스테이션' },
  { icon: 'circuit', title: '전자, IoT', desc: '센서, Arduino, Raspberry Pi' },
  { icon: 'tools', title: '메이커, 건축', desc: '측정 도구, 제작 장비' }
]
const benefits = [
  { number: '01', title: '재고가 보이면 바로 대여', desc: '자산 운영자가 보유 수량과 신청을 같은 흐름에서 관리합니다.' },
  { number: '02', title: '도입 요청은 사람의 근거로', desc: '구성원이 필요성을 설명하고 그룹 관리자와 학교 관리자가 순서대로 검토합니다.' },
  { number: '03', title: 'AI는 관리자 의사결정에', desc: '기준선과 모델 성능을 공개하고 수요, 재고, 대여기간을 함께 비교합니다.' }
]
</script>

<style scoped>
.landing { background: #fff; }
.hero { position: relative; overflow: hidden; margin: 18px; padding: 86px 0 82px; background: linear-gradient(135deg, #edf5ff 0%, #f8fbff 62%, #eef4ff 100%); border: 1px solid rgba(190, 211, 241, .78); border-radius: var(--radius-xl); }
.hero::after { content: ''; position: absolute; width: 430px; height: 430px; right: -170px; top: -210px; border: 70px solid rgba(37, 99, 235, .06); border-radius: 50%; }
.hero-grid { position: relative; z-index: 1; display: grid; grid-template-columns: 1.08fr .92fr; align-items: center; gap: 70px; }
.eyebrow i { width: 7px; height: 7px; background: var(--color-accent); border-radius: 50%; }
.hero h1 { color: var(--color-navy); font-family: var(--font-display); font-size: clamp(40px, 4.6vw, 59px); line-height: 1.16; letter-spacing: -.055em; word-break: keep-all; }
.hero h1 em { color: var(--color-primary); font-style: normal; }
.hero-copy > p { max-width: 570px; margin-top: 22px; color: var(--color-text-secondary); font-size: 16px; line-height: 1.8; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 30px; }
.hero-actions em { color: #bfdbfe; font-style: normal; }
.trust-row { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 27px; color: var(--color-text-secondary); font-size: 11px; font-weight: 600; }
.trust-row span { display: inline-flex; align-items: center; gap: 4px; }
.workflow-card { padding: 26px; background: rgba(255,255,255,.88); border: 1px solid rgba(190, 211, 241, .86); border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); backdrop-filter: blur(16px); }
.workflow-head { display: flex; align-items: center; justify-content: space-between; }
.workflow-head div { display: flex; flex-direction: column; }
.workflow-head strong { margin-top: 2px; color: var(--color-navy); font-size: 17px; }
.live-dot { color: var(--color-success); background: var(--color-success-light); border-radius: 999px; padding: 5px 9px; font-size: 10px; font-weight: 700; }
.workflow-list { display: flex; flex-direction: column; gap: 10px; margin: 23px 0; }
.workflow-item { display: grid; grid-template-columns: 26px 38px 1fr auto; align-items: center; gap: 11px; padding: 13px; background: rgba(244, 248, 255, .88); border: 1px solid #dbe7f7; border-radius: 11px; animation: fadeInUp var(--duration-slow) var(--ease-out) both; animation-delay: calc(180ms + var(--delay)); transition: var(--transition); }
.workflow-item:hover { transform: translateX(4px); border-color: var(--color-border-hover); background: #fff; }
.step { color: var(--color-text-muted); font-size: 9px; font-weight: 800; }
.workflow-icon { width: 36px; height: 36px; display: grid; place-items: center; color: var(--color-primary); background: var(--color-primary-light); border-radius: 10px; font-size: 17px; }
.workflow-item div { display: flex; flex-direction: column; }
.workflow-item strong { font-size: 12px; }
.workflow-item small { color: var(--color-text-muted); font-size: 10px; }
.arrow { color: #7894bd; }
.category-section { padding: 64px 0; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 28px; }
.section-heading h2, .why-copy h2 { color: var(--color-navy); font-size: clamp(27px, 3vw, 38px); line-height: 1.25; letter-spacing: -.04em; }
.text-link { color: var(--color-primary); font-size: 12px; font-weight: 700; }
.category-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.category-card { display: flex; align-items: center; gap: 15px; padding: 21px; background: linear-gradient(145deg, rgba(255,255,255,.96), rgba(240,246,255,.86)); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); transition: var(--transition); }
.category-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }
.category-card > span { width: 43px; height: 43px; flex: 0 0 43px; display: grid; place-items: center; color: var(--color-primary); background: #fff; border-radius: 12px; box-shadow: var(--shadow-sm); font-size: 21px; }
.category-card h3 { font-size: 13px; }
.category-card p { margin-top: 3px; color: var(--color-text-muted); font-size: 10px; line-height: 1.5; }
.why-section { width: min(1180px, calc(100% - 48px)); margin: 10px auto 32px; padding: 56px 0; color: var(--color-text-primary); background: linear-gradient(125deg, #edf5ff, #f8fbff); border: 1px solid #d6e4f7; border-radius: var(--radius-xl); }
.why-section .container { width: min(1060px, calc(100% - 64px)); }
.why-grid { display: grid; grid-template-columns: .85fr 1.15fr; gap: 90px; align-items: center; }
.why-copy .eyebrow { color: var(--color-primary); }
.why-copy h2 { color: var(--color-text-primary); }
.why-copy p { margin-top: 18px; color: var(--color-text-secondary); font-size: 14px; line-height: 1.8; }
.benefit-list { display: flex; flex-direction: column; gap: 10px; }
.benefit { display: grid; grid-template-columns: 42px 1fr; gap: 16px; padding: 17px 19px; background: rgba(255,255,255,.82); border: 1px solid #d8e5f6; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); transition: var(--transition); }
.benefit:hover { transform: translateX(5px); box-shadow: var(--shadow-md); }
.benefit > span { color: var(--color-primary); font-size: 11px; font-weight: 800; }
.benefit strong { font-size: 14px; }
.benefit p { margin-top: 4px; color: var(--color-text-secondary); font-size: 11px; }
footer { padding: 24px 0; background: #fff; color: var(--color-text-muted); border-top: 1px solid var(--color-border); }
footer .container { display: flex; justify-content: space-between; font-size: 10px; }
footer strong { color: var(--color-text-primary); font-size: 12px; }
.reveal { animation: landingReveal 680ms var(--ease-out) both; }
.reveal-delay-1 { animation-delay: 120ms; }
.reveal-section { opacity: 0; transform: translateY(28px); transition: opacity 680ms var(--ease-out), transform 680ms var(--ease-out); }
.reveal-section.is-visible { opacity: 1; transform: translateY(0); }
.reveal-section .reveal-item { opacity: 0; transform: translateY(18px); }
.reveal-section.is-visible .reveal-item { animation: landingReveal 560ms var(--ease-out) both; animation-delay: var(--item-delay); }
@keyframes landingReveal { from { opacity: 0; transform: translateY(22px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 850px) {
  .hero { padding: 56px 0; }
  .hero-grid, .why-grid { grid-template-columns: 1fr; gap: 42px; }
  .category-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 520px) {
  .category-grid { grid-template-columns: 1fr; }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 12px; }
  footer .container { align-items: flex-start; flex-direction: column; gap: 4px; }
}
</style>
