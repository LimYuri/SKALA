import api from './index.js'

export const paymentApi = {
  getPending(groupId) {
    return api.get('/api/payments', { params: { status: 'PENDING', groupId } })
  },
  approve(paymentId) {
    return api.post(`/api/payments/${paymentId}/approve`)
  },
  reject(paymentId) {
    return api.post(`/api/payments/${paymentId}/reject`)
  }
}
