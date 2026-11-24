import { useEffect, useRef } from 'react'

const SITEKEY = import.meta.env.VITE_TURNSTILE_SITEKEY || ''
const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

let scriptPromise = null
function loadScript() {
  if (window.turnstile) return Promise.resolve(window.turnstile)
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = SCRIPT_SRC
      s.async = true
      s.defer = true
      s.onload = () => resolve(window.turnstile)
      s.onerror = () => { scriptPromise = null; reject(new Error('turnstile load failed')) }
      document.head.appendChild(s)
    })
  }
  return scriptPromise
}

export const turnstileEnabled = Boolean(SITEKEY)

/**
 * Cloudflare Turnstile 자리. 사이트키(VITE_TURNSTILE_SITEKEY)가 없으면 아무것도 그리지 않는다.
 * 토큰은 한 번 쓰면 끝이라, 부모가 resetKey를 바꾸면 새 토큰을 받는다.
 */
export default function TurnstileWidget({ onToken, resetKey }) {
  const box = useRef(null)
  const widgetId = useRef(null)
  const cb = useRef(onToken)
  useEffect(() => { cb.current = onToken }, [onToken])

  useEffect(() => {
    if (!SITEKEY) return
    let cancelled = false
    loadScript().then((ts) => {
      if (cancelled || !box.current || widgetId.current !== null) return
      widgetId.current = ts.render(box.current, {
        sitekey: SITEKEY,
        size: 'flexible',
        appearance: 'interaction-only',
        callback: (t) => cb.current?.(t),
        'expired-callback': () => cb.current?.(''),
        'error-callback': () => cb.current?.(''),
      })
    }).catch(() => cb.current?.(''))
    return () => {
      cancelled = true
      if (widgetId.current !== null && window.turnstile) {
        try { window.turnstile.remove(widgetId.current) } catch { /* 이미 사라짐 */ }
      }
      widgetId.current = null
    }
  }, [])

  useEffect(() => {
    if (!SITEKEY || resetKey === undefined || widgetId.current === null || !window.turnstile) return
    try { window.turnstile.reset(widgetId.current) } catch { /* 무시 */ }
  }, [resetKey])

  if (!SITEKEY) return null
  return <div ref={box} className="px-3 pt-2" aria-label="봇 확인" />
}
