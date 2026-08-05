// 한국관광공사 TourAPI (공공데이터포털)
import axios from 'axios'

const API_KEY = import.meta.env.VITE_TOUR_API_KEY ?? ''

// data.go.kr 응답이 느려 타임아웃 15초로 설정
const client = axios.create({ baseURL: 'https://apis.data.go.kr/B551011/KorService2', timeout: 15000 })

// 관광지 종류(contentTypeId) -> 문구/아이콘
const CONTENT_TYPES = {
  12: { label: '관광지', icon: '🏞️' },
  14: { label: '문화시설', icon: '🏛️' },
  15: { label: '축제/행사', icon: '🎉' },
  25: { label: '여행코스', icon: '🗺️' },
  28: { label: '레포츠', icon: '🚴' },
  32: { label: '숙박', icon: '🏨' },
  38: { label: '쇼핑', icon: '🛍️' },
  39: { label: '음식점', icon: '🍽️' },
}

// 근처 관광정보 조회 (contentTypeId 지정 시 해당 종류만)
export async function fetchNearbyAttractions(city, { radius = 5000, contentTypeId = '' } = {}) {
  if (!API_KEY || !city) return []

  const { data } = await client.get('/locationBasedList2', {
    params: {
      serviceKey: API_KEY,
      numOfRows: 20,
      pageNo: 1,
      MobileOS: 'ETC',
      MobileApp: 'SkalaVueWeather',
      _type: 'json',
      arrange: 'E', // 거리순 정렬
      mapX: city.longitude,
      mapY: city.latitude,
      radius,
      contentTypeId,
    },
  })

  const header = data?.response?.header
  if (header && header.resultCode !== '0000' && header.resultCode !== '00') return []

  const items = data?.response?.body?.items?.item
  if (!items) return []
  const list = Array.isArray(items) ? items : [items]

  return list.map((item) => {
    const type = CONTENT_TYPES[item.contenttypeid] ?? { label: '기타', icon: '📍' }
    return {
      title: item.title || '이름 정보 없음',
      typeLabel: type.label,
      icon: type.icon,
      address: item.addr1 || '',
      image: item.firstimage || '',
      distanceMeters: item.dist ? Math.round(Number(item.dist)) : undefined,
    }
  })
}

export { CONTENT_TYPES }
