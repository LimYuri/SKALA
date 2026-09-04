import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { groupApi } from '@/api/group.js'

export const useGroupStore = defineStore('group', () => {
  const groups = ref([])
  const currentGroup = ref(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref('')

  const isManager = computed(() => currentGroup.value?.currentRole === 'MANAGER')

  async function fetchGroups() {
    loading.value = true
    error.value = ''
    try {
      const response = await groupApi.getMyGroups()
      groups.value = response.data?.data ?? []
      loaded.value = true
      const savedId = Number(sessionStorage.getItem('current_group_id'))
      if (!currentGroup.value && savedId) {
        currentGroup.value = groups.value.find(group => group.id === savedId) ?? null
      }
      return groups.value
    } catch (cause) {
      groups.value = []
      loaded.value = false
      error.value = cause.response?.data?.message || cause.response?.data?.detail || '그룹 목록을 불러오지 못했습니다.'
      throw cause
    } finally {
      loading.value = false
    }
  }

  async function loadGroup(groupId) {
    const numericId = Number(groupId)
    let found = groups.value.find(group => group.id === numericId)
    if (!found) {
      const response = await groupApi.getById(numericId)
      found = response.data?.data ?? response.data
      if (found && !groups.value.some(group => group.id === found.id)) groups.value.push(found)
    }
    selectGroup(found)
    return found
  }

  function selectGroup(group) {
    currentGroup.value = group || null
    if (group?.id) sessionStorage.setItem('current_group_id', String(group.id))
    else sessionStorage.removeItem('current_group_id')
  }

  function clear() {
    groups.value = []
    currentGroup.value = null
    loaded.value = false
    sessionStorage.removeItem('current_group_id')
  }

  return { groups, currentGroup, loading, loaded, error, isManager, fetchGroups, loadGroup, selectGroup, clear }
})
