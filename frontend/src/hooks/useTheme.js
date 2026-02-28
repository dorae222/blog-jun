import { create } from 'zustand'

const useTheme = create((set) => ({
  dark: false,
  toggle: () =>
    set((state) => {
      const next = !state.dark
      document.documentElement.classList.toggle('dark', next)
      localStorage.setItem('theme', next ? 'dark' : 'light')
      return { dark: next }
    }),
  init: () => {
    const saved = localStorage.getItem('theme')
    const dark = saved === 'dark'
    document.documentElement.classList.toggle('dark', dark)
    set({ dark })
  },
}))

export default useTheme
