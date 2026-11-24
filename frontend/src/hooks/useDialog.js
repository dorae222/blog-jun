import { create } from 'zustand'

/**
 * 브라우저 confirm()/prompt() 대신 쓰는 약속(Promise) 기반 대화상자.
 *   if (!(await confirmDialog({ title, message, variant: 'danger' }))) return
 *   const url = await promptDialog({ title: '링크 넣기', placeholder: 'https://' })  // 취소면 null
 * 실제 화면은 App에 한 번 붙인 <DialogHost />가 그린다. 한 번에 하나만 띄우고, 겹치면 앞의 것을 취소로 닫는다.
 */
const useDialog = create((set, get) => ({
  current: null, // { kind: 'confirm'|'prompt', options, resolve }
  open(kind, options) {
    const prev = get().current
    if (prev) prev.resolve(kind === 'confirm' ? false : null)
    return new Promise((resolve) => set({ current: { kind, options: options || {}, resolve } }))
  },
  close(value) {
    const cur = get().current
    if (!cur) return
    set({ current: null })
    cur.resolve(value)
  },
}))

export const confirmDialog = (options) => useDialog.getState().open('confirm', options)
export const promptDialog = (options) => useDialog.getState().open('prompt', options)

export default useDialog
