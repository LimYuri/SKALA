// 건강보험심사평가원 병원정보서비스/약국정보서비스 (공공데이터포털)
import axios from 'axios'

// 두 서비스가 같은 기관 인증키를 공용으로 사용
const API_KEY = import.meta.env.VITE_HIRA_API_KEY ?? ''

// data.go.kr 응답이 느려 타임아웃 15초로 설정
const client = axios.create({ baseURL: 'https://apis.data.go.kr/B551182', timeout: 15000 })

// 병원/약국 공통 조회 로직
async function fetchNearby(servicePath, city, radius) {
  if (!API_KEY || !city) return []

  // 서비스별 활용신청 안 된 경우 403 + 별도 에러 응답이 옴
  let data
  try {
    ;({ data } = await client.get(`/${servicePath}`, {
      params: {
        serviceKey: API_KEY,
        pageNo: 1,
        numOfRows: 20,
        _type: 'json',
        xPos: city.longitude,
        yPos: city.latitude,
        radius, // 단위: 미터(m)
      },
    }))
  } catch (error) {
    const serviceError = error.response?.data?.OpenAPI_ServiceResponse?.cmmMsgHeader
    if (serviceError) throw new Error(`이 서비스는 별도 활용신청이 필요합니다(${serviceError.returnAuthMsg || serviceError.errMsg}).`, { cause: error })
    throw error
  }

  const serviceError = data?.OpenAPI_ServiceResponse?.cmmMsgHeader
  if (serviceError) throw new Error(`이 서비스는 별도 활용신청이 필요합니다(${serviceError.returnAuthMsg || serviceError.errMsg}).`)

  const header = data?.response?.header
  if (header && header.resultCode !== '00') return []

  const items = data?.response?.body?.items?.item
  if (!items) return []
  const list = Array.isArray(items) ? items : [items]

  // 거리순 정렬 (distance 없으면 0 취급)
  return list
    .map((item) => ({
      name: item.yadmNm || item.dutyName || '이름 정보 없음',
      address: item.addr || item.dutyAddr || '',
      phone: item.telno || item.dutyTel1 || '',
      distanceMeters: item.distance ? Math.round(Number(item.distance)) : undefined,
    }))
    .sort((a, b) => (a.distanceMeters ?? 0) - (b.distanceMeters ?? 0))
}

// 근처 병원 목록
export function fetchNearbyHospitals(city, radius = 3000) {
  return fetchNearby('hospInfoServicev2/getHospBasisList', city, radius)
}

// 근처 약국 목록
export function fetchNearbyPharmacies(city, radius = 3000) {
  return fetchNearby('pharmacyInfoService/getParmacyBasisList', city, radius)
}
