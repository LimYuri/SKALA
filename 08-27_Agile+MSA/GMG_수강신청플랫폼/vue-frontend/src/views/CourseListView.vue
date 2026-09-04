<template>
  <div class="page-shell">
    <AppHeader />
    <main class="page-main">
      <div class="container">
        <div class="page-heading">
          <div>
            <span class="eyebrow">{{ group?.name || 'GROUP' }}, ASSET CATALOG</span>
            <h1 class="page-title">대여 자산 찾기</h1>
            <p class="page-subtitle">학교 공용 자산과 이 그룹의 전용 자산을 재고, 종류, 대여 조건으로 찾아보세요.</p>
          </div>
          <div class="heading-actions">
            <router-link v-if="!isManager" :to="path('/acquisitions/new')" class="btn btn-outline">미보유 장비 요청</router-link>
            <router-link v-if="isManager" :to="path('/assets/new')" class="btn btn-primary">보유 자산 등록</router-link>
          </div>
        </div>

        <section class="catalog-summary" aria-label="자산 요약">
          <div><strong>{{ stats.total }}</strong><span>조회 자산</span></div>
          <div><strong>{{ stats.available }}</strong><span>대여 가능</span></div>
          <div><strong>{{ stats.organization }}</strong><span>학교 공용</span></div>
          <div><strong>{{ stats.group }}</strong><span>그룹 전용</span></div>
        </section>

        <section class="search-surface surface" aria-label="자산 검색과 필터">
          <label class="search-field">
            <span class="sr-only">자산 검색</span>
            <AppIcon name="search" :size="18" class="search-icon" />
            <input
              v-model.trim="keyword"
              type="search"
              placeholder="자산명, 설명, 대여 장소 검색"
              autocomplete="off"
            />
          </label>
          <label class="availability-check">
            <input v-model="availableOnly" type="checkbox" />
            <span>대여 가능한 것만</span>
          </label>
          <label class="compact-select">
            <span>범위</span>
            <select v-model="scopeFilter" aria-label="자산 범위">
              <option value="ALL">전체</option>
              <option value="ORGANIZATION">학교 공용</option>
              <option value="GROUP">그룹 전용</option>
            </select>
          </label>
          <label class="compact-select">
            <span>정렬</span>
            <select v-model="sortBy" aria-label="자산 정렬">
              <option value="RECOMMENDED">추천순</option>
              <option value="AVAILABLE">재고 많은 순</option>
              <option value="NAME">이름순</option>
              <option value="PERIOD">대여기간 긴 순</option>
            </select>
          </label>
        </section>

        <div class="category-tabs" role="group" aria-label="자산 카테고리">
          <button
            v-for="category in categories"
            :key="category.value"
            :class="['category-tab', { active: selectedCategory === category.value }]"
            :aria-pressed="selectedCategory === category.value"
            @click="selectCategory(category.value)"
          >
            <AppIcon :name="category.icon" :size="16" />{{ category.label }}
          </button>
        </div>

        <div class="result-line">
          <span><strong>{{ filteredCourses.length }}</strong>개 자산</span>
          <button v-if="hasFilters" class="clear-filter" @click="clearFilters">필터 초기화</button>
          <span v-if="courseStore.error" class="load-error">{{ courseStore.error }}</span>
        </div>

        <div v-if="loading" class="loading-state surface">
          <div class="spinner"></div>
          <span>자산과 재고를 불러오고 있습니다.</span>
        </div>
        <div v-else-if="visibleCourses.length" class="gear-grid fade-in-up">
          <CourseCard
            v-for="course in visibleCourses"
            :key="course.id"
            :course="course"
            :group-id="groupId"
          />
        </div>
        <div v-else class="empty-state surface">
          <span class="empty-icon"><AppIcon name="search" :size="30" /></span>
          <strong>조건에 맞는 자산이 없습니다.</strong>
          <p>{{ isManager ? '필터 조건을 줄이거나 새로운 자산을 등록해 보세요.' : '필터를 줄이거나 미보유 장비 도입 요청을 시작해 보세요.' }}</p>
          <div class="empty-actions">
            <button class="btn btn-ghost" @click="clearFilters">필터 초기화</button>
            <router-link v-if="!isManager" :to="path('/acquisitions/new')" class="btn btn-outline">도입 요청</router-link>
            <router-link v-else :to="path('/assets/new')" class="btn btn-primary">보유 자산 등록</router-link>
          </div>
        </div>

        <div v-if="visibleCourses.length < filteredCourses.length" class="load-more">
          <button class="btn btn-ghost" @click="visibleLimit += 12">
            자산 더 보기, {{ filteredCourses.length - visibleCourses.length }}개 남음
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppIcon from '@/components/AppIcon.vue'
import CourseCard from '@/components/CourseCard.vue'
import { useAuthStore } from '@/store/auth.js'
import { useCourseStore } from '@/store/course.js'
import { useGroupStore } from '@/store/group.js'

const route = useRoute()
const auth = useAuthStore()
const courseStore = useCourseStore()
const groupStore = useGroupStore()

const groupId = computed(() => Number(route.params.groupId))
const group = computed(() => groupStore.currentGroup)
const keyword = ref('')
const availableOnly = ref(false)
const scopeFilter = ref('ALL')
const sortBy = ref('RECOMMENDED')
const visibleLimit = ref(12)

const isManager = computed(() => auth.isInstructor || group.value?.currentRole === 'MANAGER')
const categories = computed(() => courseStore.categories)
const loading = computed(() => courseStore.loading)
const selectedCategory = computed(() => courseStore.selectedCategory)

const stats = computed(() => ({
  total: courseStore.courses.length,
  available: courseStore.courses.filter(course => Number(course.availableQuantity) > 0).length,
  organization: courseStore.courses.filter(course => course.visibility === 'ORGANIZATION').length,
  group: courseStore.courses.filter(course => course.visibility === 'GROUP').length
}))

const filteredCourses = computed(() => {
  const needle = keyword.value.toLowerCase()
  const filtered = courseStore.courses.filter(course => (
    (selectedCategory.value === 'ALL' || course.categoryCode === selectedCategory.value)
    && (scopeFilter.value === 'ALL' || course.visibility === scopeFilter.value)
    && (!needle || `${course.title} ${course.description || ''} ${course.pickupLocation || ''}`.toLowerCase().includes(needle))
    && (!availableOnly.value || Number(course.availableQuantity) > 0)
  ))

  return [...filtered].sort((a, b) => {
    if (sortBy.value === 'NAME') return a.title.localeCompare(b.title, 'ko')
    if (sortBy.value === 'PERIOD') return Number(b.maxLoanDays || 0) - Number(a.maxLoanDays || 0)
    if (sortBy.value === 'AVAILABLE') return Number(b.availableQuantity || 0) - Number(a.availableQuantity || 0)
    const availability = Number(b.availableQuantity > 0) - Number(a.availableQuantity > 0)
    if (availability !== 0) return availability
    return Number(b.availableQuantity || 0) - Number(a.availableQuantity || 0)
  })
})

const visibleCourses = computed(() => filteredCourses.value.slice(0, visibleLimit.value))
const hasFilters = computed(() => (
  keyword.value
  || availableOnly.value
  || scopeFilter.value !== 'ALL'
  || selectedCategory.value !== 'ALL'
  || sortBy.value !== 'RECOMMENDED'
))

const path = suffix => `/groups/${groupId.value}${suffix}`

function selectCategory(category) {
  courseStore.setCategory(category)
}

function applyQuery() {
  const category = String(route.query.category || 'ALL')
  const validCategory = courseStore.categories.some(item => item.value === category) ? category : 'ALL'
  courseStore.setCategory(validCategory)
  keyword.value = String(route.query.q || '')
  availableOnly.value = route.query.available === '1'
  scopeFilter.value = ['ORGANIZATION', 'GROUP'].includes(route.query.scope) ? route.query.scope : 'ALL'
}

function clearFilters() {
  keyword.value = ''
  availableOnly.value = false
  scopeFilter.value = 'ALL'
  sortBy.value = 'RECOMMENDED'
  courseStore.setCategory('ALL')
}

async function load() {
  await groupStore.loadGroup(groupId.value).catch(() => {})
  await courseStore.fetchCourses(groupId.value)
}

watch([keyword, availableOnly, scopeFilter, sortBy, selectedCategory], () => {
  visibleLimit.value = 12
})
watch(() => route.query, applyQuery)
watch(groupId, load)

onMounted(() => {
  applyQuery()
  load()
})
</script>

<style scoped>
.heading-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 9px;
}
.catalog-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 14px;
}
.catalog-summary > div {
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 11px 14px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, .72);
  border: 1px solid var(--color-border);
  border-radius: 11px;
}
.catalog-summary strong {
  color: var(--color-navy);
  font-size: 18px;
}
.catalog-summary span { font-size: 11px; }
.search-surface {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto 150px 160px;
  align-items: end;
  gap: 12px;
  padding: 15px;
}
.search-field {
  position: relative;
}
.search-field input {
  width: 100%;
  height: 46px;
  padding: 0 15px 0 42px;
  background: var(--color-bg-secondary);
  border: 1px solid transparent;
  border-radius: 11px;
  outline: none;
  font-size: 13px;
}
.search-field input:focus {
  background: #fff;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}
.search-icon {
  position: absolute;
  top: 11px;
  left: 15px;
  z-index: 1;
  color: var(--color-primary);
  font-size: 18px;
}
.availability-check {
  height: 46px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 3px;
  white-space: nowrap;
}
.availability-check input {
  width: 17px;
  height: 17px;
  accent-color: var(--color-primary);
}
.availability-check span {
  font-size: 12px;
  font-weight: 650;
}
.compact-select {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.compact-select span {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
}
.compact-select select {
  height: 40px;
  padding: 0 9px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 9px;
  font-size: 11px;
}
.category-tabs {
  display: flex;
  gap: 7px;
  margin-top: 16px;
  padding-bottom: 4px;
  overflow-x: auto;
}
.category-tab {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 13px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, .72);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.category-tab.active {
  color: #fff;
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  box-shadow: 0 6px 14px rgba(37, 99, 235, .16);
}
.result-line {
  min-height: 42px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  color: var(--color-text-muted);
  font-size: 12px;
}
.result-line strong {
  color: var(--color-primary);
  font-size: 17px;
}
.clear-filter {
  color: var(--color-primary);
  background: transparent;
  border: 0;
  font-size: 11px;
  font-weight: 700;
}
.load-error {
  margin-left: auto;
  color: var(--color-danger);
}
.gear-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.empty-actions {
  display: flex;
  gap: 8px;
}
.load-more {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 980px) {
  .search-surface { grid-template-columns: 1fr 1fr; }
  .search-field { grid-column: 1 / -1; }
  .gear-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 680px) {
  .heading-actions { justify-content: flex-start; }
  .catalog-summary { grid-template-columns: repeat(2, 1fr); }
  .search-surface { grid-template-columns: 1fr; align-items: stretch; }
  .search-field { grid-column: auto; }
  .availability-check { height: 36px; }
  .gear-grid { grid-template-columns: 1fr; }
}
</style>
