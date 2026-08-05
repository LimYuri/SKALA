import axios from 'axios'
// 강수 레이더 API (별도 무료 API, 키 불필요)
import { fetchRadarFrames } from './weatherApi'

// OpenWeatherMap API 키 (환경변수, 없으면 기본값)
const API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY ?? '717bd53025bf8efe557db9b7ae858d25'

// axios 인스턴스 생성, 8초 타임아웃
const owmClient = axios.create({ baseURL: import.meta.env.VITE_OPENWEATHER_API_URL ?? 'https://api.openweathermap.org', timeout: 8000 })

// 날씨 코드 -> 한글 텍스트
export const weatherCodeText = (code) => {
  const id = Number(code)
  if (id === 800) return '맑음'
  if (id === 801) return '대체로 맑음'
  if (id === 802) return '부분적으로 흐림'
  if (id === 803 || id === 804) return '흐림'
  if (id >= 200 && id <= 232) return '뇌우'
  if (id >= 300 && id <= 321) return '이슬비'
  if (id >= 500 && id <= 504) return '비'
  if (id === 511) return '어는 비'
  if (id >= 520 && id <= 531) return '소나기'
  if (id >= 600 && id <= 622) return '눈'
  if (id >= 701 && id <= 781) return '안개·연무'
  return '알 수 없음'
}

// 날씨 코드 -> 이모지 아이콘
export const weatherCodeIcon = (code) => {
  const id = Number(code)
  if (id === 800) return '☀️'
  if (id === 801 || id === 802) return '🌤️'
  if (id === 803 || id === 804) return '☁️'
  if (id >= 200 && id <= 232) return '⛈️'
  if (id >= 300 && id <= 321) return '🌦️'
  if ((id >= 500 && id <= 504) || (id >= 520 && id <= 531)) return '🌧️'
  if (id >= 600 && id <= 622) return '🌨️'
  if (id >= 701 && id <= 781) return '🌫️'
  return '🌡️'
}

// 대기질 지수 -> 한글 등급
export const airQualityText = (aqi) => {
  const level = Number(aqi)
  if (level === 1) return '좋음'
  if (level === 2) return '보통'
  if (level === 3) return '민감군 주의'
  if (level === 4) return '나쁨'
  if (level === 5) return '매우 나쁨'
  return '정보 없음'
}

// 체감온도 구간별 옷차림 추천
export const clothingRecommendation = (feels) => {
  const t = Number(feels)
  if (t >= 28) return { icon: '🩳', title: '민소매·반바지', desc: '가장 얇고 시원한 옷차림으로 충분해요.' }
  if (t >= 23) return { icon: '👕', title: '반팔·얇은 셔츠', desc: '통풍 잘 되는 소재의 옷을 추천해요.' }
  if (t >= 20) return { icon: '🧥', title: '얇은 가디건·긴팔', desc: '아침저녁 기온차를 대비해 겉옷 하나만 챙기세요.' }
  if (t >= 17) return { icon: '🧶', title: '니트·맨투맨', desc: '얇은 니트 한 장 정도면 딱 좋은 날씨예요.' }
  if (t >= 12) return { icon: '🧥', title: '자켓·트렌치코트', desc: '가벼운 겉옷이 필요한 선선한 날씨예요.' }
  if (t >= 9) return { icon: '🧣', title: '코트·니트', desc: '조금 도톰한 겉옷과 목도리를 준비하세요.' }
  if (t >= 5) return { icon: '🧤', title: '두꺼운 코트·장갑', desc: '방한용품 없이는 쌀쌀하게 느껴질 거예요.' }
  return { icon: '🥶', title: '패딩·두꺼운 아우터', desc: '최대한 두껍게 챙겨 입고 나가세요.' }
}

// 체감온도·강수확률·날씨코드 기반 음식 추천
export const foodRecommendation = (feels, rain, code) => {
  const t = Number(feels)
  const isRainy = Number(rain) >= 60 || (Number(code) >= 200 && Number(code) <= 622)
  if (isRainy) return { icon: '🥘', title: '파전·뜨끈한 국물 요리', desc: '비 오는 날엔 부침개나 얼큰한 국물이 생각나죠.' }
  if (t >= 30) return { icon: '🍉', title: '냉면·삼계탕', desc: '더위엔 시원한 냉면이나 보양식인 삼계탕이 좋아요.' }
  if (t >= 25) return { icon: '🍧', title: '냉국수·빙수', desc: '몸을 시원하게 식혀주는 메뉴를 추천해요.' }
  if (t <= 5) return { icon: '🍲', title: '찌개·탕 요리', desc: '추운 날엔 뜨끈한 국물 요리로 몸을 녹여보세요.' }
  return { icon: '🍱', title: '제철 든든한 한 끼', desc: '덥지도 춥지도 않은 날, 평소 좋아하는 메뉴 어때요.' }
}

// 기온·습도·바람·강수·미세먼지 종합 쾌적지수 (0~100점)
export const comfortScore = (weather) => {
  const temp = weather.current.temp
  const humidity = weather.current.humidity
  const wind = weather.current.wind
  const rain = weather.daily?.[0]?.rain ?? 0
  const aqi = weather.current.air?.aqi ?? 0

  let score = 100
  score -= Math.min(40, Math.abs(temp - 22) * 2.2)
  score -= Math.max(0, humidity - 60) * 0.6
  score -= Math.max(0, 40 - humidity) * 0.5
  score -= Math.max(0, wind - 20) * 0.8
  score -= rain * 0.35
  if (aqi) score -= (aqi - 1) * 7
  score = Math.round(Math.max(0, Math.min(100, score)))

  let level = 'poor'
  let label = '매우 나쁨'
  if (score >= 85) {
    level = 'best'
    label = '최적'
  } else if (score >= 70) {
    level = 'good'
    label = '좋음'
  } else if (score >= 50) {
    level = 'okay'
    label = '보통'
  } else if (score >= 30) {
    level = 'bad'
    label = '나쁨'
  }

  return { score, level, label }
}

// 일출·일몰 시각과 낮 경과율 계산
export function sunPositionInfo(current, today) {
  const toMinutes = (localIso) => {
    if (!localIso) return null
    const hour = Number(localIso.slice(11, 13))
    const minute = Number(localIso.slice(14, 16))
    return hour * 60 + minute
  }
  const nowMinutes = toMinutes(current?.observedAt)
  const sunriseMinutes = toMinutes(today?.sunrise)
  const sunsetMinutes = toMinutes(today?.sunset)
  if (nowMinutes === null || sunriseMinutes === null || sunsetMinutes === null) {
    return { sunriseLabel: '-', sunsetLabel: '-', percent: 0, isDaytime: true, remainingLabel: '' }
  }
  const dayLength = sunsetMinutes - sunriseMinutes || 1
  const percent = Math.min(100, Math.max(0, Math.round(((nowMinutes - sunriseMinutes) / dayLength) * 100)))
  const isDaytime = nowMinutes >= sunriseMinutes && nowMinutes <= sunsetMinutes
  const minutesLeft = isDaytime ? sunsetMinutes - nowMinutes : null
  const remainingLabel = minutesLeft === null ? '' : `일몰까지 ${Math.floor(minutesLeft / 60)}시간 ${minutesLeft % 60}분`
  const toLabel = (localIso) => localIso.slice(11, 16)
  return { sunriseLabel: toLabel(today.sunrise), sunsetLabel: toLabel(today.sunset), percent, isDaytime, remainingLabel }
}

// 기상청 기준값 참고한 자체 판단 폭염/한파/강풍/호우/대설 경보
export function severeWeatherWarnings(daily) {
  const today = daily?.[0]
  if (!today) return []
  const warnings = []

  // 폭염: 주의보 33℃↑, 경보 35℃↑
  if (today.max >= 35) warnings.push({ level: 'warning', icon: '🥵', title: '폭염경보', text: `오늘 최고기온이 ${today.max}℃로 예상됩니다. 한낮 야외활동을 최대한 피하세요.` })
  else if (today.max >= 33) warnings.push({ level: 'watch', icon: '🌡️', title: '폭염주의보', text: `오늘 최고기온이 ${today.max}℃로 예상됩니다. 수분 섭취와 그늘에서의 휴식이 필요해요.` })

  // 한파: 주의보 -12℃↓, 경보 -15℃↓
  if (today.min <= -15) warnings.push({ level: 'warning', icon: '🥶', title: '한파경보', text: `오늘 최저기온이 ${today.min}℃로 예상됩니다. 노출 부위 동상에 유의하세요.` })
  else if (today.min <= -12) warnings.push({ level: 'watch', icon: '❄️', title: '한파주의보', text: `오늘 최저기온이 ${today.min}℃로 예상됩니다. 방한용품을 꼭 챙기세요.` })

  // 강풍: 주의보 50.4km/h↑, 경보 75.6km/h↑
  if (today.windGustMax >= 75.6)
    warnings.push({ level: 'warning', icon: '🌪️', title: '강풍경보', text: `최대 순간풍속이 ${today.windGustMax}km/h로 예상됩니다. 야외 시설물과 간판에 각별히 주의하세요.` })
  else if (today.windGustMax >= 50.4)
    warnings.push({ level: 'watch', icon: '💨', title: '강풍주의보', text: `최대 순간풍속이 ${today.windGustMax}km/h로 예상됩니다. 강풍에 날아갈 수 있는 물건을 치워두세요.` })

  // 호우: 주의보 110mm↑, 경보 180mm↑
  if (today.precipitation >= 180) warnings.push({ level: 'warning', icon: '🌊', title: '호우경보', text: `오늘 누적 강수량이 ${today.precipitation}mm로 예상됩니다. 침수·범람 지역 접근을 피하세요.` })
  else if (today.precipitation >= 110)
    warnings.push({ level: 'watch', icon: '☔', title: '호우주의보', text: `오늘 누적 강수량이 ${today.precipitation}mm로 예상됩니다. 저지대·지하공간 이용에 주의하세요.` })

  // 대설: 주의보 5cm↑, 경보 20cm↑
  if (today.snowAccum >= 20) warnings.push({ level: 'warning', icon: '☃️', title: '대설경보', text: `오늘 예상 적설량이 약 ${today.snowAccum}cm입니다. 도로 결빙과 시설물 붕괴에 주의하세요.` })
  else if (today.snowAccum >= 5) warnings.push({ level: 'watch', icon: '🌨️', title: '대설주의보', text: `오늘 예상 적설량이 약 ${today.snowAccum}cm입니다. 제설 전까지 운전을 자제하세요.` })

  // 장마 유사 패턴: 3일 연속 강수확률 60% 이상
  const upcoming = daily.slice(0, 3)
  if (upcoming.length === 3 && upcoming.every((day) => day.rain >= 60)) {
    warnings.push({ level: 'watch', icon: '🌧️', title: '장마철 유사 패턴 (참고용)', text: '앞으로 3일간 강수확률이 계속 60% 이상으로 예보되어, 장마철과 비슷하게 비가 이어질 가능성이 있어요.' })
  }

  return warnings
}

// 풍향(도) -> 8방위 텍스트
export const windDirectionText = (degree) => {
  const directions = ['북', '북동', '동', '남동', '남', '남서', '서', '북서']
  return directions[Math.round(Number(degree) / 45) % directions.length] ?? '-'
}

// UTC 타임스탬프 -> 도시 로컬시각 문자열 변환
function toLocalIsoMinute(unixSeconds, timezoneOffsetSeconds) {
  const localMs = (Number(unixSeconds) + Number(timezoneOffsetSeconds ?? 0)) * 1000
  return new Date(localMs).toISOString().slice(0, 16)
}

// 도시 이름으로 검색 (지오코딩)
export async function searchCities(keyword) {
  const { data } = await owmClient.get('/geo/1.0/direct', {
    params: { q: keyword, limit: 8, appid: API_KEY },
  })
  return (
    (data ?? [])
      .filter((place) => Number.isFinite(place.lat) && Number.isFinite(place.lon))
      // 국내(KR) 지역만 허용
      .filter((place) => place.country === 'KR')
      .map((place) => {
        const koreanName = place.local_names?.ko
        const name = koreanName || place.name
        return {
          id: `${place.lat.toFixed(4)},${place.lon.toFixed(4)}`,
          name,
          country: place.country ?? '-',
          countryCode: place.country ?? '',
          admin: place.state || '',
          type: '지도 지역',
          latitude: place.lat,
          longitude: place.lon,
          displayAddress: [name, place.state, place.country].filter(Boolean).join(', '),
        }
      })
      .map((city) => ({ ...city, id: cityKey(city) }))
      // 좌표 중복 제거
      .filter((city, index, list) => index === list.findIndex((item) => item.id === city.id))
      .slice(0, 10)
  )
}

// 현재 위치 -> 도시 정보 (역지오코딩)
export function locateMyCity() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('이 브라우저는 위치 정보 기능을 지원하지 않습니다.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords
          const { data } = await owmClient.get('/geo/1.0/reverse', {
            params: { lat: latitude, lon: longitude, limit: 1, appid: API_KEY },
          })
          const place = data?.[0]
          // 국내(KR) 지역만 허용
          if (place && place.country !== 'KR') {
            reject(new Error('국내 지역에서만 이용할 수 있는 서비스입니다.'))
            return
          }
          const name = place?.local_names?.ko || place?.name || '내 위치'
          resolve({
            id: cityKey({ latitude, longitude }),
            name,
            country: place?.country ?? '-',
            countryCode: place?.country ?? '',
            admin: place?.state || '',
            type: '현재 위치',
            latitude,
            longitude,
            displayAddress: [name, place?.state, place?.country].filter(Boolean).join(', '),
          })
        } catch (error) {
          reject(error)
        }
      },
      (geoError) => reject(new Error(geoError.message || '위치 정보를 가져오지 못했습니다.')),
      { timeout: 8000 },
    )
  })
}

// 현재 날씨 + 5일 예보 조회
export async function fetchWeather(city) {
  if (!city || !Number.isFinite(Number(city.latitude)) || !Number.isFinite(Number(city.longitude))) {
    throw new Error('날씨 요청에 필요한 지역 좌표가 없습니다.')
  }
  const params = { lat: city.latitude, lon: city.longitude, appid: API_KEY, units: 'metric', lang: 'kr' }

  // 현재 날씨 + 예보 + 대기질 병렬 요청
  const [{ data: current }, { data: forecast }, air] = await Promise.all([
    owmClient.get('/data/2.5/weather', { params }),
    owmClient.get('/data/2.5/forecast', { params }),
    owmClient.get('/data/2.5/air_pollution', { params }).catch(() => null),
  ])

  if (!current?.weather?.length || !Array.isArray(forecast?.list)) {
    throw new Error('날씨 API 응답 형식이 올바르지 않습니다.')
  }

  const timezoneOffset = forecast.city?.timezone ?? 0
  const airSample = air?.data?.list?.[0]

  // 3시간 단위 예보를 날짜별로 그룹화
  const dailyMap = new Map()
  forecast.list.forEach((slot) => {
    const localIso = toLocalIsoMinute(slot.dt, timezoneOffset)
    const date = localIso.slice(0, 10)
    const hour = Number(localIso.slice(11, 13))
    if (!dailyMap.has(date)) dailyMap.set(date, [])
    dailyMap.get(date).push({ ...slot, hour })
  })

  // 날짜별 요약(최고/최저/강수/적설/습도 등) 계산
  const daily = [...dailyMap.entries()].map(([date, slots]) => {
    const noonSlot = slots.reduce((closest, slot) => (Math.abs(slot.hour - 12) < Math.abs(closest.hour - 12) ? slot : closest), slots[0])
    return {
      date,
      code: noonSlot.weather[0].id,
      max: Math.round(Math.max(...slots.map((slot) => slot.main.temp_max))),
      min: Math.round(Math.min(...slots.map((slot) => slot.main.temp_min))),
      rain: Math.round(Math.max(...slots.map((slot) => (slot.pop ?? 0) * 100))),
      precipitation: Math.round(slots.reduce((sum, slot) => sum + (slot.rain?.['3h'] ?? 0), 0) * 10) / 10,
      snowAccum: Math.round(slots.reduce((sum, slot) => sum + (slot.snow?.['3h'] ?? 0), 0) * 10) / 10,
      humidity: Math.round(slots.reduce((sum, slot) => sum + slot.main.humidity, 0) / slots.length),
      uvIndex: 0,
      sunrise: toLocalIsoMinute(current.sys.sunrise, timezoneOffset),
      sunset: toLocalIsoMinute(current.sys.sunset, timezoneOffset),
      windMax: Math.round(Math.max(...slots.map((slot) => slot.wind.speed * 3.6)) * 10) / 10,
      windGustMax: Math.round(Math.max(...slots.map((slot) => (slot.wind.gust ?? slot.wind.speed) * 3.6)) * 10) / 10,
      hourly: slots.map((slot) => ({
        time: toLocalIsoMinute(slot.dt, timezoneOffset).slice(11, 16),
        code: slot.weather[0].id,
        temp: Math.round(slot.main.temp),
        rain: Math.round((slot.pop ?? 0) * 100),
      })),
    }
  })

  return {
    city: { ...city, id: cityKey(city) },
    current: {
      temp: Math.round(current.main.temp),
      feels: Math.round(current.main.feels_like),
      humidity: current.main.humidity,
      wind: Math.round(current.wind.speed * 3.6 * 10) / 10,
      windDirection: current.wind.deg ?? 0,
      windGust: Math.round((current.wind.gust ?? current.wind.speed) * 3.6 * 10) / 10,
      precipitation: current.rain?.['1h'] ?? 0,
      rain: current.rain?.['1h'] ?? 0,
      cloudCover: current.clouds?.all ?? 0,
      pressure: Math.round(current.main.pressure),
      surfacePressure: Math.round(current.main.grnd_level ?? current.main.pressure),
      visibility: Math.round((current.visibility ?? 10000) / 100) / 10,
      uvIndex: 0,
      code: current.weather[0].id,
      observedAt: toLocalIsoMinute(current.dt, timezoneOffset),
      air: {
        aqi: airSample?.main?.aqi ?? 0,
        pm2_5: Math.round(airSample?.components?.pm2_5 ?? 0),
        pm10: Math.round(airSample?.components?.pm10 ?? 0),
      },
    },
    daily,
  }
}

// 좌표 기반 고유 id 생성
export const cityKey = (city) => `${Number(city.latitude).toFixed(4)},${Number(city.longitude).toFixed(4)}`

// 도시 객체 -> 라우터 query 변환
export const cityToQuery = (city, prefix = '') => ({
  [`${prefix}Name`]: city.name,
  [`${prefix}Country`]: city.country,
  [`${prefix}Admin`]: city.admin || undefined,
  [`${prefix}Lat`]: String(city.latitude),
  [`${prefix}Lon`]: String(city.longitude),
})

// 라우터 query -> 도시 객체 복원
export const cityFromQuery = (query, prefix = '') => {
  const name = query[`${prefix}Name`]
  const country = query[`${prefix}Country`]
  const latitude = Number(query[`${prefix}Lat`])
  const longitude = Number(query[`${prefix}Lon`])
  if (typeof name !== 'string' || !name || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  const city = {
    name,
    country: typeof country === 'string' ? country : '-',
    admin: typeof query[`${prefix}Admin`] === 'string' ? query[`${prefix}Admin`] : '',
    latitude,
    longitude,
  }
  return { ...city, id: cityKey(city) }
}

// 레이더 함수 재노출
export { fetchRadarFrames }
