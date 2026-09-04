import { defineStore } from 'pinia'
import { ref } from 'vue'
import { courseApi } from '@/api/course.js'

export const categoryOptions = [
  { value: 'ALL', label: '전체', icon: 'grid' },
  { value: 'DEVICE', label: '스마트기기', icon: 'device' },
  { value: 'COMPUTER', label: '컴퓨터', icon: 'computer' },
  { value: 'SERVER_CLOUD', label: '서버, 클라우드', icon: 'cloud' },
  { value: 'ELECTRONICS_IOT', label: '전자, IoT', icon: 'circuit' },
  { value: 'MAKER', label: '메이커, 건축', icon: 'tools' },
  { value: 'CAMERA_AUDIO', label: '촬영, 음향', icon: 'camera' },
  { value: 'PRESENTATION', label: '발표, 행사', icon: 'presentation' },
  { value: 'ACCESSORY', label: '부속품', icon: 'accessory' },
  { value: 'ETC', label: '기타', icon: 'plus' }
]

const legacyLabels = {
  BACKEND: '개발장비',
  FRONTEND: '디자인장비',
  DEVOPS: '서버, 클라우드',
  DATA_SCIENCE: '데이터장비',
  MOBILE: '스마트기기',
  SECURITY: '보안장비',
  DATABASE: '데이터장비',
  OTHER: '기타'
}

export function categoryLabel(code) {
  return categoryOptions.find(item => item.value === code)?.label || legacyLabels[code] || code || '기타'
}

export function categoryIcon(codeOrLabel) {
  const option = categoryOptions.find(item => item.value === codeOrLabel || item.label === codeOrLabel)
  if (option) return option.icon
  const legacy = Object.entries(legacyLabels).find(([, label]) => label === codeOrLabel)
  return legacy ? 'grid' : 'plus'
}

export const useCourseStore = defineStore('course', () => {
  const courses = ref([])
  const selectedCourse = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const selectedCategory = ref('ALL')

  function normalizeCourse(course) {
    if (!course || typeof course !== 'object') return course
    const categoryCode = course.categoryCode || course.category
    return {
      ...course,
      categoryCode,
      category: categoryLabel(categoryCode),
      totalQuantity: Number(course.totalQuantity ?? 1),
      availableQuantity: Number(course.availableQuantity ?? 1),
      enrollmentCount: Number(course.enrollmentCount ?? 0),
      itemType: course.itemType || 'OWNED'
    }
  }

  async function fetchCourses(groupId) {
    loading.value = true
    error.value = null
    try {
      const res = await courseApi.getAll(groupId ? { groupId } : undefined)
      const raw = Array.isArray(res.data?.data)
        ? res.data.data
        : Array.isArray(res.data) ? res.data : []
      courses.value = raw.map(normalizeCourse)
    } catch (e) {
      error.value = e.response?.data?.message || '자산 목록을 불러오지 못했습니다.'
      courses.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchCourse(id) {
    loading.value = true
    error.value = null
    try {
      const res = await courseApi.getById(id)
      selectedCourse.value = normalizeCourse(res.data?.data ?? res.data)
    } catch (e) {
      error.value = e.response?.data?.message || '자산 정보를 불러오지 못했습니다.'
      selectedCourse.value = null
    } finally {
      loading.value = false
    }
  }

  function setCategory(category) {
    selectedCategory.value = category
  }

  return {
    courses,
    selectedCourse,
    loading,
    error,
    selectedCategory,
    categories: categoryOptions,
    normalizeCourse,
    fetchCourses,
    fetchCourse,
    setCategory
  }
})
