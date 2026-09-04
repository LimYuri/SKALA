<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <template v-if="isManager">
          <div class="page-heading">
            <div>
              <p class="page-subtitle">과거 요청량과 대여기간을 학습해 부족 가능성을 찾고, 이동 검토 또는 도입 요청으로 바로 연결합니다.</p>
            </div>
            <button class="btn btn-primary" :disabled="training || loading" @click="askTraining = true">
              {{ training ? '학습 중...' : '모델 다시 학습' }}
            </button>
          </div>

          <div v-if="error" class="error-box feedback" role="alert">{{ error }}</div>
          <div v-if="message" class="success-box feedback" role="status">{{ message }}</div>

          <div v-if="loading" class="loading-state surface">
            <div class="spinner"></div>
            <span>예측 결과와 모델 평가를 불러오고 있습니다.</span>
          </div>

          <template v-else-if="forecast">
            <section class="decision-brief surface">
              <div class="brief-icon" aria-hidden="true"><AppIcon name="sparkle" :size="24" /></div>
              <div>
                <span>이번 4주 운영 요약</span>
                <h2>{{ decisionBrief }}</h2>
              </div>
              <small>생성 {{ trainedAt }}</small>
            </section>

            <section class="executive-grid" aria-label="수요예측 핵심 지표">
              <div class="executive-card surface">
                <span>부족 카테고리</span>
                <strong class="danger">{{ riskCount('HIGH') }}</strong>
                <small>전체 {{ forecast.items.length }}개 중</small>
              </div>
              <div class="executive-card surface">
                <span>예상 부족 수량</span>
                <strong>{{ totalShortage }}개</strong>
                <small>4주 필요 재고 기준</small>
              </div>
              <div class="executive-card surface">
                <span>이동 검토 가능</span>
                <strong>{{ transferableCount }}</strong>
                <small>타 그룹 잉여 재고 존재</small>
              </div>
              <div class="executive-card surface model-highlight">
                <span>기준선 대비 개선</span>
                <strong>{{ signed(evaluation?.improvementPercent) }}</strong>
                <small>WAPE가 낮을수록 정확</small>
              </div>
            </section>

            <section class="model-strip surface">
              <div>
                <small>선택 모델</small>
                <strong>{{ modelName }}</strong>
                <span>검증 기간 WAPE가 가장 낮은 모델</span>
              </div>
              <div>
                <small>학습 이벤트</small>
                <strong>{{ evaluation?.eventCount?.toLocaleString() || '—' }}건</strong>
                <span>{{ evaluation?.dataStart }} ~ {{ evaluation?.dataEnd }}</span>
              </div>
              <div>
                <small>단순 기준선 WAPE</small>
                <strong>{{ pct(evaluation?.baselineWape) }}</strong>
                <span>최근 4주 이동평균</span>
              </div>
              <div class="model-result">
                <small>선택 모델 WAPE</small>
                <strong>{{ pct(evaluation?.modelWape) }}</strong>
                <span>{{ modelVerdict }}</span>
              </div>
            </section>

            <div class="forecast-toolbar">
              <div class="risk-summary" role="group" aria-label="위험 단계 필터">
                <button :class="{ active: riskFilter === 'ALL' }" :aria-pressed="riskFilter === 'ALL'" @click="riskFilter = 'ALL'">전체 {{ forecast.items.length }}</button>
                <button class="risk-high" :class="{ active: riskFilter === 'HIGH' }" :aria-pressed="riskFilter === 'HIGH'" @click="riskFilter = 'HIGH'">부족 {{ riskCount('HIGH') }}</button>
                <button class="risk-medium" :class="{ active: riskFilter === 'MEDIUM' }" :aria-pressed="riskFilter === 'MEDIUM'" @click="riskFilter = 'MEDIUM'">주의 {{ riskCount('MEDIUM') }}</button>
                <button class="risk-low" :class="{ active: riskFilter === 'LOW' }" :aria-pressed="riskFilter === 'LOW'" @click="riskFilter = 'LOW'">안정 {{ riskCount('LOW') }}</button>
              </div>
              <span>부족 위험과 수량이 큰 순서로 표시합니다.</span>
            </div>

            <div v-if="filteredItems.length" class="forecast-grid">
              <article v-for="item in filteredItems" :key="item.category" class="forecast-card surface">
                <div class="forecast-head">
                  <div>
                    <span class="category-symbol" aria-hidden="true"><AppIcon :name="categoryIcon(item.category)" :size="22" /></span>
                    <div><small>{{ item.category }}</small><h2>{{ categoryLabel(item.category) }}</h2></div>
                  </div>
                  <span :class="['risk-pill', `risk-${item.riskLevel.toLowerCase()}`]">{{ riskLabel(item.riskLevel) }}</span>
                </div>

                <dl class="numbers">
                  <div><dt>4주 예상 요청</dt><dd>{{ item.forecastDemand }}건</dd></div>
                  <div><dt>평균 대여기간</dt><dd>{{ item.averageLoanDays }}일</dd></div>
                  <div><dt>필요 수량</dt><dd>{{ item.requiredUnits }}개</dd></div>
                  <div><dt>현재 재고</dt><dd>{{ item.totalStock }}개</dd></div>
                  <div><dt>현재 가용</dt><dd>{{ item.availableStock }}개</dd></div>
                  <div><dt>예상 부족</dt><dd :class="{ shortage: item.shortageUnits > 0 }">{{ item.shortageUnits }}개</dd></div>
                </dl>

                <div class="chart" role="img" :aria-label="`${categoryLabel(item.category)} 주별 예상 요청`">
                  <div v-for="week in item.weekly" :key="week.weekStart" class="bar-column">
                    <span>{{ week.predictedDemand }}</span>
                    <div class="bar-track"><i :style="{ height: barHeight(item, week) }"></i></div>
                    <small>{{ weekLabel(week.weekStart) }}</small>
                  </div>
                </div>

                <div v-if="item.transferSuggestions.length" class="recommendation transfer">
                  <div>
                    <strong>먼저 그룹 간 이동 검토</strong>
                    <span>구매 전 타 그룹의 잉여 재고를 확인하세요.</span>
                  </div>
                  <router-link
                    v-for="suggestion in item.transferSuggestions"
                    :key="suggestion.fromGroupId"
                    :to="transferLink(suggestion, item)"
                  >
                    {{ groupName(suggestion.fromGroupId) }}, {{ suggestion.suggestedQuantity }}개 확인 →
                  </router-link>
                </div>
                <div v-else-if="item.shortageUnits > 0" class="recommendation purchase">
                  <div>
                    <strong>도입 검토 권장</strong>
                    <span>이동 가능한 타 그룹 잉여 재고가 없습니다.</span>
                  </div>
                  <router-link :to="acquisitionLink(item)">근거를 이어서 도입 요청 작성 →</router-link>
                </div>
                <div v-else class="recommendation stable">
                  <div>
                    <strong>추가 도입 불필요</strong>
                    <span>예측 수요를 현재 재고로 감당할 수 있습니다.</span>
                  </div>
                  <router-link :to="assetLink(item)">현재 자산 확인 →</router-link>
                </div>
              </article>
            </div>

            <div v-else class="empty-state surface">
              <strong>선택한 위험 단계의 카테고리가 없습니다.</strong>
              <button class="btn btn-ghost" @click="riskFilter = 'ALL'">전체 결과 보기</button>
            </div>

            <details class="model-details surface">
              <summary>
                <div>
                  <strong>모델 검증과 후보 비교 보기</strong>
                  <span>시간순 데이터 분리와 후보별 검증 WAPE를 확인합니다.</span>
                </div>
                <b aria-hidden="true"><AppIcon name="plus" :size="18" /></b>
              </summary>
              <div class="model-detail-body">
                <section class="method">
                  <div><span>1</span><strong>데이터 집계</strong><p>18개월 요청 이벤트를 그룹×카테고리×주 단위로 집계합니다.</p></div>
                  <div><span>2</span><strong>시간순 분리</strong><p>미래 정보가 학습에 섞이지 않도록 학습, 검증, 테스트를 나눕니다.</p></div>
                  <div><span>3</span><strong>모델 선택</strong><p>Poisson, Random Forest, Gradient Boosting을 검증 WAPE로 비교합니다.</p></div>
                  <div><span>4</span><strong>업무 연결</strong><p>예상 수요, 대여기간, 재고를 결합해 이동 또는 도입을 제안합니다.</p></div>
                </section>
                <div v-if="candidateRows.length" class="model-table-wrap" tabindex="0" aria-label="모델 후보 평가표, 가로로 스크롤할 수 있습니다.">
                  <table class="model-table">
                    <thead><tr><th>후보</th><th>검증 WAPE</th><th>테스트 WAPE</th><th>선택</th></tr></thead>
                    <tbody>
                      <tr v-for="row in candidateRows" :key="row.name">
                        <td>{{ candidateName(row.name) }}</td>
                        <td>{{ pct(row.validationWape) }}</td>
                        <td>{{ pct(row.testWape) }}</td>
                        <td>{{ row.name === (evaluation?.modelName || forecast.modelName) ? '✓ 선택' : '' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </details>
          </template>
        </template>

        <div v-else class="empty-state surface">
          <strong>그룹 관리자만 수요예측을 볼 수 있습니다.</strong>
          <router-link :to="`/groups/${groupId}`" class="btn btn-outline">그룹 홈</router-link>
        </div>
      </div>
    </main>

    <ConfirmDialog
      :open="askTraining"
      title="수요예측 모델을 다시 학습할까요?"
      description="누적된 대여 요청 이벤트로 후보 모델을 다시 비교하고 최신 4주 예측을 생성합니다. 완료까지 잠시 걸릴 수 있습니다."
      confirm-label="다시 학습"
      @cancel="askTraining = false"
      @confirm="train"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { analyticsApi } from '@/api/analytics.js'
import { useAuthStore } from '@/store/auth.js'
import { categoryIcon, categoryLabel } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'
import { formatApiDateTime, formatLocalDate } from '@/utils/datetime.js'

const route = useRoute()
const auth = useAuthStore()
const groupStore = useGroupStore()
const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const isManager = computed(() => auth.isInstructor || group.value?.currentRole === 'MANAGER')
const forecast = ref(null)
const evaluation = ref(null)
const loading = ref(true)
const training = ref(false)
const askTraining = ref(false)
const error = ref('')
const message = ref('')
const riskFilter = ref('ALL')

const filteredItems = computed(() => (
  (forecast.value?.items || [])
    .filter(item => riskFilter.value === 'ALL' || item.riskLevel === riskFilter.value)
    .sort((a, b) => {
      const riskOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 }
      return riskOrder[a.riskLevel] - riskOrder[b.riskLevel] || b.shortageUnits - a.shortageUnits
    })
))
const modelName = computed(() => candidateName(evaluation.value?.modelName || forecast.value?.modelName))
const totalShortage = computed(() => forecast.value?.items?.reduce((sum, item) => sum + Number(item.shortageUnits || 0), 0) || 0)
const transferableCount = computed(() => forecast.value?.items?.filter(item => item.transferSuggestions?.length).length || 0)
const trainedAt = computed(() => formatApiDateTime(evaluation.value?.trainedAt || forecast.value?.generatedAt))
const decisionBrief = computed(() => {
  const high = riskCount('HIGH')
  if (!high) return '현재 재고로 예측 수요를 감당할 수 있습니다.'
  if (transferableCount.value) return `${high}개 카테고리에서 부족이 예상되며, ${transferableCount.value}개는 그룹 간 이동을 먼저 검토할 수 있습니다.`
  return `${high}개 카테고리에서 총 ${totalShortage.value}개 재고 부족이 예상되어 도입 검토가 필요합니다.`
})
const modelVerdict = computed(() => (
  Number(evaluation.value?.improvementPercent || 0) >= 0
    ? `기준선보다 ${Number(evaluation.value?.improvementPercent || 0).toFixed(1)}% 개선`
    : '기준선보다 낮은 성능 — 의사결정에 주의'
))
const candidateRows = computed(() => Object.entries(evaluation.value?.candidateMetrics || {}).map(([name, metrics]) => ({
  name,
  validationWape: metrics?.validation?.wape,
  testWape: metrics?.test?.wape
})))

const pct = value => value == null ? '—' : `${Number(value).toFixed(1)}%`
const signed = value => value == null ? '—' : `${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(1)}%`
const riskCount = risk => forecast.value?.items?.filter(item => item.riskLevel === risk).length || 0
const riskLabel = risk => ({ HIGH: '부족', MEDIUM: '주의', LOW: '안정' })[risk] || risk
const weekLabel = value => formatLocalDate(value, { month: 'numeric', day: 'numeric' })
const barHeight = (item, week) => {
  const max = Math.max(...item.weekly.map(row => Number(row.predictedDemand)), 1)
  return `${Math.max(8, Number(week.predictedDemand) / max * 100)}%`
}
const groupName = id => groupStore.groups.find(row => Number(row.id) === Number(id))?.name || `그룹 #${id}`

function candidateName(name) {
  return ({
    poisson_regression: 'Poisson 회귀',
    random_forest: 'Random Forest',
    hist_gradient_boosting: 'Histogram Gradient Boosting',
    rolling_mean_4_baseline: '최근 4주 이동평균'
  })[name] || name || '—'
}

function transferLink(suggestion, item) {
  return {
    path: `/groups/${suggestion.fromGroupId}/assets`,
    query: { category: item.category, available: '1' }
  }
}

function acquisitionLink(item) {
  return {
    path: `/groups/${groupId.value}/acquisitions/new`,
    query: {
      source: 'ai',
      category: item.category,
      title: `${categoryLabel(item.category)} 장비 도입`,
      quantity: Math.max(1, Number(item.shortageUnits || 1)),
      reason: `${group.value?.name || '우리 그룹'}의 향후 4주 ${categoryLabel(item.category)} 수요는 ${item.forecastDemand}건이며, 필요 ${item.requiredUnits}개 대비 현재 재고 ${item.totalStock}개로 ${item.shortageUnits}개 부족이 예상됩니다.`
    }
  }
}

function assetLink(item) {
  return {
    path: `/groups/${groupId.value}/assets`,
    query: { category: item.category, available: '1' }
  }
}

const explain = cause => cause.response?.data?.detail || cause.response?.data?.message || '수요예측 결과를 불러오지 못했습니다.'

async function load() {
  loading.value = true
  error.value = ''
  try {
    await groupStore.loadGroup(groupId.value)
    if (!isManager.value) return
    if (!groupStore.groups.length) await groupStore.fetchGroups()
    const [forecastResponse, evaluationResponse] = await Promise.all([
      analyticsApi.getForecast(groupId.value),
      analyticsApi.getEvaluation()
    ])
    forecast.value = forecastResponse.data
    evaluation.value = evaluationResponse.data
  } catch (cause) {
    error.value = explain(cause)
  } finally {
    loading.value = false
  }
}

async function train() {
  askTraining.value = false
  training.value = true
  error.value = ''
  message.value = ''
  try {
    const response = await analyticsApi.train()
    message.value = `${candidateName(response.data.modelName)} 학습을 완료했습니다. 분석 이력 ${Number(response.data.eventCount).toLocaleString()}건을 사용했습니다.`
    await load()
  } catch (cause) {
    error.value = explain(cause)
  } finally {
    training.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.ai-eyebrow { color: var(--color-ai); }
.feedback { margin-bottom: 14px; }
.decision-brief {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
  padding: 20px;
  color: var(--color-text-primary);
  background: linear-gradient(125deg, rgba(234, 242, 255, .96), rgba(247, 250, 255, .94));
  border: 1px solid #d4e2f5;
}
.brief-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: rgba(255, 255, 255, .86);
  border-radius: 14px;
  font-size: 20px;
}
.decision-brief span { color: var(--color-ai); font-size: 9px; font-weight: 800; letter-spacing: .08em; }
.decision-brief h2 { margin-top: 3px; font-size: 17px; line-height: 1.45; }
.decision-brief p { margin-top: 3px; color: var(--color-text-secondary); font-size: 10px; }
.decision-brief > small { color: var(--color-text-muted); font-size: 9px; white-space: nowrap; }
.executive-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 11px;
  margin-bottom: 14px;
}
.executive-card {
  display: flex;
  flex-direction: column;
  padding: 17px;
}
.executive-card > span { color: var(--color-text-muted); font-size: 10px; }
.executive-card strong { margin-top: 3px; color: var(--color-navy); font-size: 23px; }
.executive-card strong.danger { color: var(--color-danger); }
.executive-card small { color: var(--color-text-muted); font-size: 9px; }
.model-highlight { background: var(--color-primary-light); border-color: #dce7fa; }
.model-highlight strong { color: var(--color-primary); }
.model-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 16px;
  overflow: hidden;
}
.model-strip > div {
  display: flex;
  flex-direction: column;
  padding: 18px;
  border-right: 1px solid var(--color-border);
}
.model-strip > div:last-child { border: 0; background: #f3f7ff; }
.model-strip small { color: var(--color-text-muted); font-size: 9px; }
.model-strip strong { margin: 4px 0; color: var(--color-navy); font-size: 17px; }
.model-strip span { color: var(--color-text-muted); font-size: 9px; }
.model-strip .model-result strong { color: var(--color-primary); }
.forecast-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.forecast-toolbar > span { color: var(--color-text-muted); font-size: 9px; }
.risk-summary { display: flex; gap: 7px; }
.risk-summary button {
  padding: 8px 12px;
  color: var(--color-text-secondary);
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 750;
}
.risk-summary button.active { color: #fff; background: var(--color-navy); border-color: var(--color-navy); }
.risk-summary .risk-high.active { background: var(--color-danger); border-color: var(--color-danger); }
.risk-summary .risk-medium.active { background: var(--color-warning); border-color: var(--color-warning); }
.risk-summary .risk-low.active { background: var(--color-success); border-color: var(--color-success); }
.forecast-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.forecast-card { padding: 21px; }
.forecast-head,
.forecast-head > div { display: flex; align-items: center; justify-content: space-between; }
.forecast-head > div { justify-content: flex-start; gap: 10px; }
.category-symbol {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 12px;
  font-size: 18px;
}
.forecast-head small { color: var(--color-text-muted); font-size: 8px; }
.forecast-head h2 { color: var(--color-navy); font-size: 15px; }
.risk-pill { padding: 5px 9px; border-radius: 999px; font-size: 9px; font-weight: 800; }
.risk-high { color: var(--color-danger); background: var(--color-danger-light); }
.risk-medium { color: var(--color-warning); background: var(--color-warning-light); }
.risk-low { color: var(--color-success); background: var(--color-success-light); }
.numbers {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 17px 0;
  padding: 13px;
  background: var(--color-bg-secondary);
  border-radius: 10px;
}
.numbers div { display: flex; flex-direction: column; }
.numbers dt { color: var(--color-text-muted); font-size: 9px; }
.numbers dd { margin: 2px 0 0; color: var(--color-navy); font-size: 12px; font-weight: 750; }
.numbers dd.shortage { color: var(--color-danger); }
.chart {
  height: 142px;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 12px;
  padding: 8px 12px 0;
  border-bottom: 1px solid var(--color-border);
}
.bar-column {
  height: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
}
.bar-column > span { margin-bottom: 4px; color: var(--color-text-muted); font-size: 9px; }
.bar-track {
  height: 90px;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.bar-track i {
  display: block;
  width: min(32px, 65%);
  min-height: 7px;
  background: linear-gradient(#60a5fa, #2563eb);
  border-radius: 5px 5px 0 0;
  transition: .4s;
}
.bar-column small { margin: 5px 0; color: var(--color-text-muted); font-size: 9px; }
.recommendation {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding: 12px;
  border-radius: 10px;
}
.recommendation > div { display: flex; flex-direction: column; }
.recommendation strong { font-size: 10px; }
.recommendation span { font-size: 9px; }
.recommendation a { font-size: 9px; font-weight: 800; text-align: right; }
.transfer { color: var(--color-ai); background: var(--color-ai-light); }
.purchase { color: var(--color-danger); background: var(--color-danger-light); }
.stable { color: var(--color-success); background: var(--color-success-light); }
.model-details { margin-top: 18px; overflow: hidden; }
.model-details summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  cursor: pointer;
  list-style: none;
}
.model-details summary::-webkit-details-marker { display: none; }
.model-details summary div { display: flex; flex-direction: column; }
.model-details summary strong { color: var(--color-navy); font-size: 12px; }
.model-details summary span { color: var(--color-text-muted); font-size: 9px; }
.model-details[open] summary b { transform: rotate(45deg); }
.model-detail-body {
  padding: 0 20px 20px;
  border-top: 1px solid var(--color-border);
}
.method {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 18px 0;
}
.method div {
  display: grid;
  grid-template-columns: 26px 1fr;
  column-gap: 8px;
}
.method div > span {
  grid-row: 1 / 3;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--color-primary);
  border-radius: 50%;
  font-size: 9px;
  font-weight: 800;
}
.method strong { font-size: 10px; }
.method p { margin-top: 2px; color: var(--color-text-muted); font-size: 8px; }
.model-table-wrap {
  max-width: 100%;
  overflow-x: auto;
  border-radius: var(--radius-sm);
}
.model-table-wrap:focus-visible { outline: 3px solid var(--color-primary-soft); outline-offset: 2px; }
.model-table {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;
  font-size: 10px;
}
.model-table th,
.model-table td {
  padding: 9px 10px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}
.model-table th { color: var(--color-text-muted); background: var(--color-bg-secondary); }
.model-table td:last-child { color: var(--color-primary); font-weight: 800; }

@media (max-width: 900px) {
  .executive-grid,
  .model-strip { grid-template-columns: repeat(2, 1fr); }
  .forecast-grid { grid-template-columns: 1fr; }
  .method { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .decision-brief { grid-template-columns: 42px 1fr; }
  .decision-brief > small { grid-column: 2; }
  .executive-grid,
  .model-strip,
  .method { grid-template-columns: 1fr; }
  .forecast-toolbar { align-items: flex-start; flex-direction: column; }
  .numbers { grid-template-columns: repeat(2, 1fr); }
  .recommendation { grid-template-columns: 1fr; }
  .recommendation a { text-align: left; }
}
</style>
