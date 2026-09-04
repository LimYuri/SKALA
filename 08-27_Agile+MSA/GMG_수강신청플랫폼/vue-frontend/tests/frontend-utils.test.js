import test from 'node:test'
import assert from 'node:assert/strict'

import { daysUntil, parseApiDateTime } from '../src/utils/datetime.js'
import {
  isOpenRequest,
  requestProgressIndex,
  requestSteps,
  statusMeta
} from '../src/utils/requestStatus.js'

test('시간대가 없는 서버 일시는 UTC로 해석한다', () => {
  assert.equal(parseApiDateTime('2026-08-26T22:21:00').toISOString(), '2026-08-26T22:21:00.000Z')
  assert.equal(parseApiDateTime('잘못된 날짜'), null)
})

test('반납 D-day는 시각이 아닌 날짜 경계로 계산한다', () => {
  const noon = new Date(2026, 7, 27, 12, 30)
  assert.equal(daysUntil('2026-08-27', noon), 0)
  assert.equal(daysUntil('2026-08-28', noon), 1)
  assert.equal(daysUntil('2026-08-26', noon), -1)
})

test('대여와 도입 요청의 상태·진행 단계를 구분한다', () => {
  assert.equal(statusMeta('RETURN_REQUESTED').label, '반납 확인 대기')
  assert.equal(isOpenRequest('ACTIVE'), true)
  assert.equal(isOpenRequest('RETURNED'), false)
  assert.equal(requestSteps('PURCHASE').at(-1).status, 'RECEIVED')
  assert.equal(requestProgressIndex('LOAN', 'RETURNED'), 3)
})
