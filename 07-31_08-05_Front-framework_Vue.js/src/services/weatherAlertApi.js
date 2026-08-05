// 기상청 기상특보 조회서비스 (공공데이터포털)
import axios from 'axios'
import { REGION_STATION_IDS } from '@/data/koreaRegions'

// 공공데이터포털 인증키 (없으면 빈 배열 반환)
const API_KEY = import.meta.env.VITE_KMA_API_KEY ?? ''

// data.go.kr 응답이 느려 타임아웃 15초로 설정
const client = axios.create({ baseURL: 'https://apis.data.go.kr/1360000/WthrWrnInfoService', timeout: 15000 })

// 특보 문구 키워드 -> 아이콘 매칭
function alertIcon(text) {
  if (!text) return '⚠️'
  if (text.includes('폭염')) return '🥵'
  if (text.includes('한파')) return '🥶'
  if (text.includes('호우') || text.includes('강우')) return '☔'
  if (text.includes('대설') || text.includes('눈')) return '🌨️'
  if (text.includes('강풍') || text.includes('풍랑')) return '💨'
  if (text.includes('태풍')) return '🌀'
  if (text.includes('건조')) return '🔥'
  if (text.includes('안개')) return '🌫️'
  return '⚠️'
}

// tmFc(YYYYMMDDHHmm) -> "YYYY.MM.DD HH:mm" 변환
function formatAnnouncedAt(tmFc) {
  const raw = String(tmFc ?? '')
  if (raw.length < 12) return ''
  return `${raw.slice(0, 4)}.${raw.slice(4, 6)}.${raw.slice(6, 8)} ${raw.slice(8, 10)}:${raw.slice(10, 12)}`
}

// 도시가 속한 시/도의 발효 중인 기상특보 조회
export async function fetchWeatherAlerts(city) {
  const stnId = REGION_STATION_IDS[city?.admin]
  if (!API_KEY || !stnId) return []

  const { data } = await client.get('/getWthrWrnList', {
    params: {
      serviceKey: API_KEY,
      pageNo: 1,
      numOfRows: 10,
      dataType: 'JSON',
      stnId,
    },
  })

  // resultCode가 "00"이 아니면 실패로 처리
  const header = data?.response?.header
  if (header && header.resultCode !== '00') return []

  const items = data?.response?.body?.items?.item
  if (!items) return []
  const list = Array.isArray(items) ? items : [items]

  return list.map((item) => ({
    title: item.title || '기상특보',
    icon: alertIcon(item.title),
    area: city.admin,
    announcedAt: formatAnnouncedAt(item.tmFc),
  }))
}
