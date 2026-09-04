<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <div class="page-heading">
          <div>
            <span class="eyebrow">ACQUISITION REQUEST</span>
            <h1 class="page-title">미보유 장비 도입 요청</h1>
            <p class="page-subtitle">현재 자산으로 해결하기 어려운 이유와 예상 비용을 적어 관리자 검토를 시작합니다.</p>
          </div>
        </div>

        <div v-if="fromAi" class="ai-prefill notice">
          <span aria-hidden="true"><AppIcon name="sparkle" :size="20" /></span>
          <div>
            <strong>AI 수요예측에서 시작한 요청입니다.</strong>
            <p>예측은 검토 근거를 제공할 뿐 자동으로 구매를 결정하지 않습니다. 실제 장비와 비용을 확인해 완성해 주세요.</p>
          </div>
        </div>

        <div class="request-layout">
          <section class="form-surface surface">
            <ol class="workflow" aria-label="도입 절차">
              <li class="active"><span>1</span>요청 작성</li>
              <li><span>2</span>그룹 검토</li>
              <li><span>3</span>학교 예산</li>
              <li><span>4</span>입고, 자산화</li>
            </ol>

            <form @submit.prevent="submit">
              <div class="form-grid">
                <label class="field field-full">
                  <span>장비명 <b>*</b></span>
                  <input v-model.trim="form.title" class="form-input" placeholder="예: Sony A7 IV 카메라" maxlength="120" />
                </label>
                <label class="field">
                  <span>카테고리 <b>*</b></span>
                  <select v-model="form.category" class="form-select">
                    <option disabled value="">선택하세요</option>
                    <option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label }}</option>
                  </select>
                </label>
                <label class="field">
                  <span>필요 수량 <b>*</b></span>
                  <input v-model.number="form.quantity" type="number" min="1" max="100" class="form-input" />
                </label>
                <label class="field">
                  <span>예상 단가 <b>*</b></span>
                  <input v-model.number="form.unitPrice" type="number" min="1" class="form-input" placeholder="원 단위" />
                </label>
                <div class="field">
                  <span>예상 총액</span>
                  <div class="total-field">{{ money(totalAmount) }}</div>
                </div>
                <label class="field field-full">
                  <span>구매 참고 링크 <b>*</b></span>
                  <input v-model.trim="form.purchaseUrl" type="url" class="form-input" placeholder="https:// 제조사 또는 판매 페이지" />
                  <small class="field-help">관리자가 사양과 예상 가격을 확인할 수 있는 페이지를 입력해 주세요.</small>
                </label>
                <label class="field field-full">
                  <span>필요 사양</span>
                  <textarea
                    v-model.trim="form.description"
                    class="form-textarea"
                    placeholder="모델, 성능, 함께 필요한 구성품과 호환 조건"
                    maxlength="1000"
                  ></textarea>
                </label>
                <label class="field field-full reason-field">
                  <span>도입 필요성 <b>*</b> <small class="field-hint">관리자 판단의 핵심 근거</small></span>
                  <textarea
                    v-model.trim="form.reason"
                    class="form-textarea"
                    placeholder="기존 자산으로 해결할 수 없는 이유, 예상 사용자 수, 활용 일정과 기대 효과"
                    maxlength="1000"
                  ></textarea>
                  <small class="character-count">{{ form.reason.length }}/1000</small>
                </label>
                <label class="alternative-check field-full" :class="{ checked: form.alternativeChecked }">
                  <input v-model="form.alternativeChecked" type="checkbox" />
                  <span aria-hidden="true"><AppIcon :name="form.alternativeChecked ? 'check' : 'info'" :size="17" /></span>
                  <div>
                    <strong>기존 자산과 그룹 간 이동 가능성을 확인했습니다. <b>*</b></strong>
                    <p>자산 카탈로그와 AI 이동 추천을 먼저 확인했지만 목적에 맞는 대체 장비가 없거나 수량이 부족합니다.</p>
                  </div>
                </label>
              </div>

              <div class="submission-summary">
                <div><span>도입 그룹</span><strong>{{ group?.name || `그룹 #${groupId}` }}</strong></div>
                <div><span>예상 수량</span><strong>{{ form.quantity || 0 }}개</strong></div>
                <div><span>예상 총액</span><strong>{{ money(totalAmount) }}</strong></div>
              </div>

              <div v-if="error" class="error-box feedback" role="alert">{{ error }}</div>
              <div class="form-actions">
                <router-link :to="path('/assets')" class="btn btn-ghost">취소</router-link>
                <button class="btn btn-primary" :disabled="busy">
                  {{ busy ? '제출 중...' : '도입 요청 제출' }}
                </button>
              </div>
            </form>
          </section>

          <aside class="guide-card surface">
            <span class="guide-mark" aria-hidden="true">₩</span>
            <h2>관리자가 확인할 근거</h2>
            <p>도입은 AI가 결정하지 않습니다. 요청자의 필요성과 운영 가능한 예산을 사람이 단계별로 확인합니다.</p>
            <ul>
              <li><strong>대체 가능성</strong><span>다른 그룹이나 학교 공용 자산으로 해결 가능한가?</span></li>
              <li><strong>활용 규모</strong><span>누가, 언제, 얼마나 자주 사용하는가?</span></li>
              <li><strong>비용 적정성</strong><span>수량과 사양이 목적에 비해 적절한가?</span></li>
              <li><strong>운영 계획</strong><span>입고 후 보관, 대여, 반납을 관리할 수 있는가?</span></li>
            </ul>
            <div class="guide-note">실제 결제는 발생하지 않으며, 실습에서는 예산 검토 상태만 관리합니다.</div>
          </aside>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import { enrollmentApi } from '@/api/enrollment.js'
import { categoryOptions } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'

const route = useRoute()
const router = useRouter()
const groupStore = useGroupStore()
const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const categories = categoryOptions.filter(item => item.value !== 'ALL')
const fromAi = computed(() => route.query.source === 'ai')
const form = reactive({
  title: '',
  category: '',
  quantity: 1,
  unitPrice: null,
  purchaseUrl: '',
  description: '',
  reason: '',
  alternativeChecked: false
})
const busy = ref(false)
const error = ref('')
const totalAmount = computed(() => Number(form.unitPrice || 0) * Number(form.quantity || 0))
const path = suffix => `/groups/${groupId.value}${suffix}`
const money = value => `${Number(value || 0).toLocaleString()}원`

function validate() {
  if (!form.title || !form.category || !form.purchaseUrl || !form.reason) {
    return '장비명, 카테고리, 구매 링크와 도입 필요성을 입력해 주세요.'
  }
  if (form.reason.length < 10) return '도입 필요성을 10자 이상 구체적으로 입력해 주세요.'
  if (!Number.isInteger(Number(form.quantity)) || Number(form.quantity) < 1 || Number(form.quantity) > 100) {
    return '필요 수량은 1개 이상 100개 이하로 입력해 주세요.'
  }
  if (!Number.isFinite(Number(form.unitPrice)) || Number(form.unitPrice) <= 0) return '예상 단가를 올바르게 입력해 주세요.'
  if (!/^https?:\/\//i.test(form.purchaseUrl)) return '구매 링크는 http:// 또는 https://로 시작해야 합니다.'
  if (!form.alternativeChecked) return '기존 자산과 그룹 간 이동 가능성을 확인해 주세요.'
  return ''
}

async function submit() {
  error.value = validate()
  if (error.value) return
  busy.value = true

  try {
    await enrollmentApi.requestPurchase({
      ...form,
      groupId: groupId.value,
      unitPrice: Number(form.unitPrice),
      quantity: Number(form.quantity)
    })
    router.push({ path: path('/loans'), query: { type: 'PURCHASE' } })
  } catch (cause) {
    error.value = cause.response?.data?.message || cause.response?.data?.error || '도입 요청 제출에 실패했습니다.'
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await groupStore.loadGroup(groupId.value).catch(() => {})
  const category = String(route.query.category || '')
  if (categories.some(item => item.value === category)) form.category = category
  if (route.query.title) form.title = String(route.query.title)
  const suggestedQuantity = Number(route.query.quantity)
  if (Number.isInteger(suggestedQuantity) && suggestedQuantity > 0) {
    form.quantity = Math.min(suggestedQuantity, 100)
  }
  if (route.query.reason) form.reason = String(route.query.reason)
  if (fromAi.value && !form.reason) {
    form.reason = `${group.value?.name || '우리 그룹'}의 4주 수요예측에서 ${categories.find(item => item.value === category)?.label || '해당 카테고리'} 재고 부족이 확인되어 도입을 검토합니다.`
  }
})
</script>

<style scoped>
.ai-prefill {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  margin-bottom: 16px;
}
.ai-prefill > span {
  width: 34px;
  height: 34px;
  display: grid;
  flex-shrink: 0;
  place-items: center;
  color: #fff;
  background: var(--color-ai);
  border-radius: 10px;
}
.ai-prefill strong { font-size: 12px; }
.ai-prefill p { margin-top: 2px; font-size: 10px; line-height: 1.55; }
.request-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  gap: 22px;
  align-items: start;
}
.form-surface { padding: 28px; }
.workflow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 0 0 25px;
  padding: 0;
  list-style: none;
}
.workflow li {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  color: var(--color-text-muted);
  background: var(--color-bg-secondary);
  border-radius: 9px;
  font-size: 9px;
  font-weight: 700;
}
.workflow span {
  width: 21px;
  height: 21px;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  font-size: 8px;
}
.workflow li.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.workflow li.active span {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}
.field b { color: var(--color-danger); }
.field-help {
  color: var(--color-text-muted);
  font-size: 10px;
}
.total-field {
  height: 46px;
  display: flex;
  align-items: center;
  padding: 0 13px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: var(--radius-md);
  font-weight: 800;
}
.reason-field { position: relative; }
.reason-field textarea { padding-bottom: 28px; }
.character-count {
  position: absolute;
  right: 10px;
  bottom: 7px;
  color: var(--color-text-muted);
  font-size: 9px;
}
.alternative-check {
  position: relative;
  display: grid;
  grid-template-columns: 26px 1fr;
  align-items: flex-start;
  gap: 10px;
  padding: 13px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 11px;
  cursor: pointer;
}
.alternative-check.checked {
  background: var(--color-primary-light);
  border-color: #9fbee9;
}
.alternative-check input { position: absolute; opacity: 0; }
.alternative-check:has(input:focus-visible) {
  outline: 3px solid var(--color-primary-soft);
  outline-offset: 2px;
}
.alternative-check > span {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: #fff;
  border: 1px solid #b9cdeb;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 800;
}
.alternative-check strong { color: var(--color-navy); font-size: 11px; }
.alternative-check strong b { color: var(--color-danger); }
.alternative-check p { margin-top: 3px; color: var(--color-text-muted); font-size: 9px; line-height: 1.55; }
.submission-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 20px;
  padding: 13px;
  background: var(--color-bg-secondary);
  border-radius: 11px;
}
.submission-summary div {
  display: flex;
  flex-direction: column;
}
.submission-summary span {
  color: var(--color-text-muted);
  font-size: 9px;
}
.submission-summary strong {
  margin-top: 2px;
  font-size: 11px;
}
.feedback { margin-top: 18px; }
.guide-card {
  position: sticky;
  top: 91px;
  padding: 23px;
}
.guide-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: var(--color-warning);
  background: var(--color-warning-light);
  border-radius: 12px;
  font-size: 18px;
  font-weight: 800;
}
.guide-card h2 {
  margin-top: 16px;
  color: var(--color-navy);
  font-size: 16px;
}
.guide-card > p {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1.75;
}
.guide-card ul {
  margin-top: 17px;
  padding: 15px 0 0;
  border-top: 1px solid var(--color-border);
  list-style: none;
}
.guide-card li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 7px 0;
}
.guide-card li strong { color: var(--color-navy); font-size: 10px; }
.guide-card li span { color: var(--color-text-muted); font-size: 9px; line-height: 1.5; }
.guide-note {
  margin-top: 13px;
  padding: 10px;
  color: var(--color-warning);
  background: var(--color-warning-light);
  border-radius: 9px;
  font-size: 9px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .request-layout { grid-template-columns: 1fr; }
  .guide-card { position: static; }
}
@media (max-width: 600px) {
  .form-surface { padding: 19px; }
  .workflow { grid-template-columns: repeat(2, 1fr); }
  .submission-summary { grid-template-columns: 1fr; }
}
</style>
