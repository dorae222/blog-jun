import { create } from 'zustand'

/**
 * 어디서든 여는 작업 도구(빠른 메모 등)의 열림 상태.
 * 헤더 버튼·단축키·대시보드 위젯이 같은 모달을 열어야 해서 전역으로 둔다.
 * notesVersion은 빠른 메모로 새 메모가 생겼을 때 /notes 목록과 위젯이 다시 불러오게 하는 신호다.
 */
const useWorkspace = create((set) => ({
  quickNoteOpen: false,
  notesVersion: 0,
  openQuickNote: () => set({ quickNoteOpen: true }),
  closeQuickNote: () => set({ quickNoteOpen: false }),
  bumpNotes: () => set((s) => ({ notesVersion: s.notesVersion + 1 })),
}))

export default useWorkspace
