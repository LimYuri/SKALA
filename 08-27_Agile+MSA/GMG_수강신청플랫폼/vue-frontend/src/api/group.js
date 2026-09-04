import api from './index.js'

export const groupApi = {
  getMyGroups() {
    return api.get('/api/users/groups/my')
  },
  getById(groupId) {
    return api.get(`/api/users/groups/${groupId}`)
  },
  create(data) {
    return api.post('/api/users/groups', data)
  },
  join(inviteCode) {
    return api.post('/api/users/groups/join', { inviteCode })
  },
  getMembers(groupId) {
    return api.get(`/api/users/groups/${groupId}/members`)
  },
  changeMemberRole(groupId, userId, role) {
    return api.patch(`/api/users/groups/${groupId}/members/${userId}/role`, { role })
  }
}
