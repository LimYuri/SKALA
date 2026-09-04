const DATE_TIME_WITH_ZONE = /(Z|[+-]\d{2}:?\d{2})$/i

export function parseApiDateTime(value) {
  if (!value) return null
  if (value instanceof Date) return value

  const text = String(value)
  const normalized = text.includes('T') && !DATE_TIME_WITH_ZONE.test(text)
    ? `${text}Z`
    : text
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatApiDateTime(value, options = { dateStyle: 'medium', timeStyle: 'short' }) {
  const parsed = parseApiDateTime(value)
  if (!parsed) return '-'
  return new Intl.DateTimeFormat('ko-KR', options).format(parsed)
}

export function formatApiDate(value, options = { dateStyle: 'medium' }) {
  return formatApiDateTime(value, options)
}

export function formatLocalDate(value, options = { month: 'short', day: 'numeric' }) {
  if (!value) return '-'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return '-'
  return new Intl.DateTimeFormat('ko-KR', options).format(parsed)
}

export function daysUntil(value, now = new Date()) {
  if (!value) return null
  const target = new Date(`${value}T00:00:00`)
  if (Number.isNaN(target.getTime())) return null
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.round((target.getTime() - today.getTime()) / 86400000)
}
