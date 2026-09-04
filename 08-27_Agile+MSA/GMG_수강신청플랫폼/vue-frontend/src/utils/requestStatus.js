export const REQUEST_STATUS = {
  PENDING: { label: '검토 대기', tone: 'pending', next: '그룹 관리자가 요청을 검토합니다.' },
  GROUP_APPROVED: { label: '그룹 승인', tone: 'info', next: '학교 예산 검토를 기다리고 있습니다.' },
  ACTIVE: { label: '대여 중', tone: 'active', next: '사용 후 반납 요청을 진행해 주세요.' },
  RETURN_REQUESTED: { label: '반납 확인 대기', tone: 'pending', next: '장비 전달 후 관리자가 상태를 확인합니다.' },
  RETURNED: { label: '반납 완료', tone: 'complete', next: '대여 절차가 완료되었습니다.' },
  BUDGET_APPROVED: { label: '예산 승인', tone: 'info', next: '입고와 자산 등록을 기다리고 있습니다.' },
  RECEIVED: { label: '입고 완료', tone: 'complete', next: '대여 가능한 자산으로 전환되었습니다.' },
  REJECTED: { label: '반려', tone: 'rejected', next: '검토 의견을 확인해 주세요.' },
  CANCELLED: { label: '취소', tone: 'muted', next: '요청이 종료되었습니다.' }
}

export const LOAN_STEPS = [
  { status: 'PENDING', label: '신청' },
  { status: 'ACTIVE', label: '승인, 대여' },
  { status: 'RETURN_REQUESTED', label: '반납 요청' },
  { status: 'RETURNED', label: '반납 완료' }
]

export const ACQUISITION_STEPS = [
  { status: 'PENDING', label: '요청' },
  { status: 'GROUP_APPROVED', label: '그룹 검토' },
  { status: 'BUDGET_APPROVED', label: '예산 검토' },
  { status: 'RECEIVED', label: '입고, 자산화' }
]

export function statusMeta(status) {
  return REQUEST_STATUS[status] || { label: status || '상태 미정', tone: 'muted', next: '' }
}

export function isOpenRequest(status) {
  return ['PENDING', 'GROUP_APPROVED', 'ACTIVE', 'RETURN_REQUESTED', 'BUDGET_APPROVED'].includes(status)
}

export function requestSteps(type) {
  return type === 'PURCHASE' ? ACQUISITION_STEPS : LOAN_STEPS
}

export function requestProgressIndex(type, status) {
  if (status === 'REJECTED' || status === 'CANCELLED') return -1
  const steps = requestSteps(type)
  const index = steps.findIndex(step => step.status === status)
  return index < 0 ? 0 : index
}
