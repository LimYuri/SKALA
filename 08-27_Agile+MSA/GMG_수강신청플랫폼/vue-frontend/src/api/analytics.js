import api from './index.js'

export const analyticsApi = {
  getForecast(groupId) {
    return api.get('/api/recommend/analytics/forecast', { params: { groupId } })
  },
  getEvaluation() {
    return api.get('/api/recommend/analytics/evaluation')
  },
  train() {
    return api.post('/api/recommend/analytics/train')
  }
}
