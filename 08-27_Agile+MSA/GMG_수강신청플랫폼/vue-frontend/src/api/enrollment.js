import api from './index.js'

export const enrollmentApi = {
  getMyEnrollments(groupId) {
    return api.get('/api/enrollments/my', { params: groupId ? { groupId } : {} })
  },
  enroll(data) {
    return api.post('/api/enrollments', data)
  },
  requestPurchase(data) {
    return api.post('/api/enrollments/purchases', data)
  },
  getGroupRequests(groupId, requestType, status) {
    return api.get(`/api/enrollments/group/${groupId}`, { params: { requestType, status } })
  },
  approve(enrollmentId) {
    return api.post(`/api/enrollments/${enrollmentId}/approve`)
  },
  reject(enrollmentId, reviewComment) {
    return api.post(`/api/enrollments/${enrollmentId}/reject`, { reviewComment })
  },
  approveAcquisition(enrollmentId) {
    return api.post(`/api/enrollments/${enrollmentId}/group-approve`)
  },
  requestReturn(enrollmentId) {
    return api.post(`/api/enrollments/${enrollmentId}/return-request`)
  },
  confirmReturn(enrollmentId) {
    return api.post(`/api/enrollments/${enrollmentId}/return-confirm`)
  },
  receive(enrollmentId, data) {
    return api.post(`/api/enrollments/${enrollmentId}/receive`, data)
  },
  getRecommendations(userId) {
    return api.get(`/api/recommend/${userId}`)
  },
  getAlternatives(category) {
    return api.get('/api/recommend/alternatives', { params: { category } })
  }
}
