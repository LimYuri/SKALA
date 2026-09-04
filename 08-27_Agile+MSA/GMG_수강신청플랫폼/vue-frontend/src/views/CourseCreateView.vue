<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container create-container">
        <router-link :to="path('/assets')" class="back-link">← 자산 목록</router-link>

        <div class="page-heading">
          <div>
            <span class="eyebrow">INVENTORY MANAGEMENT</span>
            <h1 class="page-title">보유 자산 등록</h1>
            <p class="page-subtitle">실제로 입고되어 즉시 대여할 수 있는 장비의 재고와 운영 조건을 등록합니다.</p>
          </div>
          <span v-if="group" class="group-context">{{ group.name }}, 관리자</span>
        </div>

        <div v-if="loading" class="loading-state surface">
          <div class="spinner"></div>
          <span>그룹 권한을 확인하고 있습니다.</span>
        </div>

        <div v-else-if="!isManager" class="empty-state surface">
          <span class="empty-icon" aria-hidden="true"><AppIcon name="alert" :size="30" /></span>
          <strong>그룹 관리자만 자산을 등록할 수 있습니다.</strong>
          <p>구성원은 미보유 장비 도입 요청을 이용해 주세요.</p>
          <router-link :to="path('')" class="btn btn-outline">그룹 홈</router-link>
        </div>

        <div v-else class="create-layout">
          <section class="form-surface surface">
            <div class="section-title">
              <span>1</span>
              <div>
                <h2>자산 정보와 대여 조건</h2>
                <p><b>*</b> 표시는 필수 입력입니다.</p>
              </div>
            </div>

            <form novalidate @submit.prevent="submit">
              <div class="form-grid">
                <label class="field field-full">
                  <span>자산명 <b>*</b></span>
                  <input
                    v-model.trim="form.title"
                    class="form-input"
                    maxlength="100"
                    placeholder="예: MacBook Pro 14 M3"
                    autocomplete="off"
                  />
                  <small class="field-help">모델이나 규격까지 적으면 구성원이 쉽게 구분할 수 있습니다.</small>
                </label>

                <label class="field field-full">
                  <span>설명 <small class="field-hint">선택</small></span>
                  <textarea
                    v-model.trim="form.description"
                    class="form-textarea"
                    maxlength="1000"
                    placeholder="주요 사양, 포함 구성품, 사용 시 주의사항을 적어 주세요."
                  ></textarea>
                  <small class="counter">{{ form.description.length }}/1000</small>
                </label>

                <label class="field">
                  <span>카테고리 <b>*</b></span>
                  <select v-model="form.category" class="form-select">
                    <option disabled value="">선택하세요</option>
                    <option v-for="item in categories" :key="item.value" :value="item.value">
                      {{ item.label }}
                    </option>
                  </select>
                </label>

                <label class="field">
                  <span>보유 수량 <b>*</b></span>
                  <div class="input-suffix">
                    <input v-model.number="form.totalQuantity" type="number" min="1" max="999" class="form-input" />
                    <span>개</span>
                  </div>
                </label>

                <label class="field">
                  <span>수령, 반납 장소 <b>*</b></span>
                  <input v-model.trim="form.pickupLocation" class="form-input" maxlength="100" placeholder="예: 공학관 301호" />
                </label>

                <label class="field">
                  <span>최대 대여기간 <b>*</b></span>
                  <div class="input-suffix">
                    <input v-model.number="form.maxLoanDays" type="number" min="1" max="60" class="form-input" />
                    <span>일</span>
                  </div>
                </label>

                <fieldset class="scope-field field-full">
                  <legend>대여 범위 <b>*</b></legend>
                  <div class="scope-options">
                    <label :class="{ selected: form.visibility === 'GROUP' }">
                      <input v-model="form.visibility" type="radio" value="GROUP" />
                      <span aria-hidden="true"><AppIcon name="home" :size="22" /></span>
                      <div>
                        <strong>{{ group?.name }} 전용</strong>
                        <small>이 그룹의 구성원만 조회하고 신청합니다.</small>
                      </div>
                    </label>
                    <label v-if="auth.isInstructor" :class="{ selected: form.visibility === 'ORGANIZATION' }">
                      <input v-model="form.visibility" type="radio" value="ORGANIZATION" />
                      <span aria-hidden="true"><AppIcon name="campus" :size="22" /></span>
                      <div>
                        <strong>학교 전체 공용</strong>
                        <small>모든 그룹에서 같은 재고를 공유합니다.</small>
                      </div>
                    </label>
                  </div>
                </fieldset>

                <label class="field">
                  <span>취득 단가 <b>*</b></span>
                  <div class="input-suffix">
                    <input v-model.number="form.price" type="number" min="0" max="1000000000" step="1000" class="form-input" />
                    <span>원</span>
                  </div>
                </label>

                <label class="field">
                  <span>참고 구매 링크 <small class="field-hint">선택</small></span>
                  <input v-model.trim="form.purchaseUrl" type="url" class="form-input" placeholder="https://..." />
                </label>
              </div>

              <div v-if="error" class="error-box feedback" role="alert">{{ error }}</div>

              <div class="form-actions">
                <router-link :to="path('/assets')" class="btn btn-ghost">취소</router-link>
                <button class="btn btn-primary" :disabled="busy">
                  {{ busy ? '등록 중...' : '재고에 자산 등록' }}
                </button>
              </div>
            </form>
          </section>

          <aside class="registration-aside">
            <section class="preview surface">
              <span class="eyebrow">REGISTRATION PREVIEW</span>
              <div class="preview-icon" aria-hidden="true"><AppIcon :name="selectedCategory?.icon || 'grid'" :size="34" /></div>
              <span class="preview-scope">{{ scopeLabel }}</span>
              <h2>{{ form.title || '등록할 자산명' }}</h2>
              <p v-if="form.description">{{ form.description }}</p>
              <dl>
                <div><dt>초기 가용</dt><dd>{{ validQuantity }}개</dd></div>
                <div><dt>최대 대여</dt><dd>{{ validLoanDays }}일</dd></div>
                <div><dt>수령, 반납</dt><dd>{{ form.pickupLocation || '장소 미입력' }}</dd></div>
                <div><dt>취득 금액</dt><dd>{{ money(totalValue) }}</dd></div>
              </dl>
            </section>
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
import { courseApi } from '@/api/course.js'
import { useAuthStore } from '@/store/auth.js'
import { categoryOptions } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const groupStore = useGroupStore()

const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const isManager = computed(() => auth.isInstructor || group.value?.currentRole === 'MANAGER')
const categories = categoryOptions.filter(item => item.value !== 'ALL')
const selectedCategory = computed(() => categories.find(item => item.value === form.category))
const loading = ref(true)
const busy = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  description: '',
  category: '',
  totalQuantity: 1,
  visibility: 'GROUP',
  maxLoanDays: 7,
  pickupLocation: '',
  price: 0,
  purchaseUrl: ''
})

const validQuantity = computed(() => Number.isInteger(Number(form.totalQuantity)) && Number(form.totalQuantity) > 0
  ? Number(form.totalQuantity)
  : 0)
const validLoanDays = computed(() => Number.isInteger(Number(form.maxLoanDays)) && Number(form.maxLoanDays) > 0
  ? Number(form.maxLoanDays)
  : 0)
const totalValue = computed(() => validQuantity.value * Math.max(0, Number(form.price || 0)))
const scopeLabel = computed(() => form.visibility === 'ORGANIZATION' ? '학교 전체 공용' : `${group.value?.name || '그룹'} 전용`)
const path = suffix => `/groups/${groupId.value}${suffix}`
const money = value => `${Number(value || 0).toLocaleString()}원`

function validate() {
  if (form.title.length < 2) return '자산명을 2자 이상 입력해 주세요.'
  if (!form.category) return '자산 카테고리를 선택해 주세요.'
  if (!Number.isInteger(Number(form.totalQuantity)) || Number(form.totalQuantity) < 1 || Number(form.totalQuantity) > 999) {
    return '보유 수량은 1개 이상 999개 이하로 입력해 주세요.'
  }
  if (!form.pickupLocation) return '구성원이 방문할 수령, 반납 장소를 입력해 주세요.'
  if (!Number.isInteger(Number(form.maxLoanDays)) || Number(form.maxLoanDays) < 1 || Number(form.maxLoanDays) > 60) {
    return '최대 대여기간은 1일 이상 60일 이하로 입력해 주세요.'
  }
  if (!Number.isFinite(Number(form.price)) || Number(form.price) < 0) return '취득 단가는 0원 이상으로 입력해 주세요.'
  if (form.purchaseUrl && !/^https?:\/\//i.test(form.purchaseUrl)) return '구매 링크는 http:// 또는 https://로 시작해야 합니다.'
  if (form.visibility === 'ORGANIZATION' && !auth.isInstructor) return '학교 공용 자산은 학교 관리자만 등록할 수 있습니다.'
  return ''
}

async function submit() {
  error.value = validate()
  if (error.value) return

  busy.value = true
  try {
    const response = await courseApi.create({
      ...form,
      itemType: 'OWNED',
      totalQuantity: Number(form.totalQuantity),
      maxLoanDays: Number(form.maxLoanDays),
      price: Number(form.price),
      ownerGroupId: form.visibility === 'GROUP' ? groupId.value : null,
      purchaseUrl: form.purchaseUrl || null
    })
    const created = response.data?.data ?? response.data
    router.push(created?.id ? path(`/assets/${created.id}`) : path('/assets'))
  } catch (cause) {
    error.value = cause.response?.data?.message || cause.response?.data?.error || '자산 등록에 실패했습니다.'
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  try {
    await groupStore.loadGroup(groupId.value)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.create-container { max-width: 1080px; }
.back-link {
  display: inline-flex;
  margin-bottom: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 700;
}
.group-context {
  padding: 7px 11px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 750;
}
.create-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 310px;
  gap: 20px;
  align-items: start;
}
.form-surface { padding: 28px; }
.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.section-title > span {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 11px;
  font-size: 13px;
  font-weight: 800;
}
.section-title h2 { color: var(--color-navy); font-size: 18px; }
.section-title p { color: var(--color-text-muted); font-size: 11px; }
.field b, .scope-field b, .section-title b { color: var(--color-danger); }
.field-help, .counter {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 500;
}
.counter { margin-top: -4px; text-align: right; }
.input-suffix { position: relative; }
.input-suffix .form-input { padding-right: 42px; }
.input-suffix > span {
  position: absolute;
  top: 50%;
  right: 13px;
  color: var(--color-text-muted);
  font-size: 11px;
  transform: translateY(-50%);
}
.scope-field { min-width: 0; border: 0; }
.scope-field legend {
  margin-bottom: 8px;
  color: #344955;
  font-size: 13px;
  font-weight: 700;
}
.scope-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.scope-options label {
  position: relative;
  display: grid;
  grid-template-columns: 34px 1fr;
  align-items: center;
  gap: 9px;
  padding: 13px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 11px;
  cursor: pointer;
}
.scope-options label.selected {
  background: var(--color-primary-light);
  border-color: #8eb4ea;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .08);
}
.scope-options input { position: absolute; opacity: 0; pointer-events: none; }
.scope-options label:has(input:focus-visible) {
  outline: 3px solid rgba(37, 99, 235, .22);
  outline-offset: 2px;
}
.scope-options label > span {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: #fff;
  border-radius: 9px;
  font-weight: 800;
}
.scope-options strong { display: block; color: var(--color-navy); font-size: 11px; }
.scope-options small { display: block; margin-top: 2px; color: var(--color-text-muted); font-size: 9px; line-height: 1.45; }
.feedback { margin-top: 18px; }
.registration-aside { position: sticky; top: 92px; display: flex; flex-direction: column; gap: 12px; }
.preview { padding: 22px; }
.preview-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  margin: 2px 0 15px;
  color: #fff;
  background: var(--color-navy);
  border-radius: 14px;
  font-size: 20px;
}
.preview-scope {
  display: inline-flex;
  padding: 4px 8px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 999px;
  font-size: 9px;
  font-weight: 750;
}
.preview h2 { margin-top: 10px; color: var(--color-navy); font-size: 17px; overflow-wrap: anywhere; }
.preview > p { min-height: 42px; margin-top: 5px; color: var(--color-text-secondary); font-size: 10px; line-height: 1.55; }
.preview dl { display: grid; gap: 9px; margin-top: 18px; padding-top: 15px; border-top: 1px solid var(--color-border); }
.preview dl > div { display: flex; justify-content: space-between; gap: 12px; }
.preview dt { color: var(--color-text-muted); font-size: 10px; }
.preview dd { color: var(--color-navy); font-size: 10px; font-weight: 750; text-align: right; }

@media (max-width: 900px) {
  .create-layout { grid-template-columns: 1fr; }
  .registration-aside { position: static; display: grid; grid-template-columns: 1fr 1fr; }
}
@media (max-width: 620px) {
  .form-surface { padding: 20px; }
  .scope-options, .registration-aside { grid-template-columns: 1fr; }
}
</style>
