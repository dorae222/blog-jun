/**
 * 손가락(굵은 포인터) 기기인지. 모바일 키보드에는 Shift+Enter가 사실상 없어서
 * Enter를 "보내기"로 쓰면 줄바꿈을 못 한다 → 터치에서는 Enter=줄바꿈, 보내기는 버튼.
 */
export const isCoarsePointer = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(pointer: coarse)').matches
