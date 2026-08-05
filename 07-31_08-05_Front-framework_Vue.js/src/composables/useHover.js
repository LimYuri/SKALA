import { ref } from 'vue'

// 카드/박스에 마우스를 올렸을 때 테두리를 강조하는 효과 적용
export function useHoverIndex() {
  const hoveredIndex = ref(-1)

  function onEnter(index) {
    hoveredIndex.value = index
  }

  function onLeave() {
    hoveredIndex.value = -1
  }

  function isHovered(index) {
    return hoveredIndex.value === index
  }

  return { hoveredIndex, onEnter, onLeave, isHovered }
}

// 카드 하나짜리 컴포넌트용 단순 호버 버전
export function useHoverFlag() {
  const isHovered = ref(false)

  function onEnter() {
    isHovered.value = true
  }

  function onLeave() {
    isHovered.value = false
  }

  return { isHovered, onEnter, onLeave }
}
