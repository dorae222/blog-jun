import { useEffect, useRef } from 'react'

/**
 * 앱 안 링크 이동 가드(가벼운 버전).
 * BrowserRouter라 react-router의 useBlocker를 쓸 수 없어서, 문서 전체의 링크 클릭을 캡처 단계에서 가로챈다.
 * 캡처 단계의 document 리스너는 React 루트 리스너보다 먼저 돌기 때문에, 여기서 막으면 <Link>의 이동도 일어나지 않는다.
 * 새 탭·수정키 클릭·다른 사이트 링크·같은 주소는 건드리지 않는다(다른 사이트로 나가는 건 beforeunload가 맡는다).
 * 뒤로 가기(popstate)는 막지 못한다 — 로컬 임시저장이 그 경우를 받친다.
 */
export default function useLeaveGuard(active, onBlocked) {
  const cb = useRef(onBlocked)
  useEffect(() => { cb.current = onBlocked }, [onBlocked])

  useEffect(() => {
    if (!active) return
    const onClick = (e) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
      const a = e.target?.closest?.('a[href]')
      if (!a || a.hasAttribute('download')) return
      if (a.target && a.target !== '_self') return
      const url = new URL(a.getAttribute('href'), window.location.href)
      if (url.origin !== window.location.origin) return
      if (url.pathname === window.location.pathname && url.search === window.location.search) return
      e.preventDefault()
      e.stopPropagation()
      cb.current?.(url.pathname + url.search + url.hash)
    }
    document.addEventListener('click', onClick, true)
    return () => document.removeEventListener('click', onClick, true)
  }, [active])
}
