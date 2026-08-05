import axios from 'axios'

// RainViewer 강수 레이더 API (키 불필요)
const radarClient = axios.create({ baseURL: import.meta.env.VITE_RADAR_API_URL, timeout: 8000 })

// 최근 레이더 프레임 목록 조회
export async function fetchRadarFrames() {
  const { data } = await radarClient.get('/public/weather-maps.json')
  const frames = data?.radar?.past
  if (!data?.host || !Array.isArray(frames) || !frames.length) throw new Error('레이더 프레임이 없습니다.')
  return { host: data.host, frames: frames.slice(-6) }
}
