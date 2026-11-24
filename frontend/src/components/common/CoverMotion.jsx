import { useEffect, useRef, useState } from 'react'

/**
 * 표지 카드 위에 얹는 움직임 층.
 *
 * 왜 표지 파일을 안 건드리고 위에 덮는가:
 * 배포된 표지는 글마다 내용에 맞춰 그린 일러스트가 들어간 PNG인데, 그걸 만든 생성기가
 * 저장소에도 git 히스토리에도 없다(pipeline/generators에 남은 것들은 전부 다른 레이아웃이다).
 * 표지를 다시 만들면 그 일러스트를 잃는다. 그래서 표지는 그대로 두고 움직임만 위에 깐다.
 * 디자인 손실이 0이고, 이 파일 하나를 지우면 원상복구된다.
 *
 * 움직이는 것: 카테고리 색의 부드러운 빛 두 덩이가 천천히 흐르고, 작은 입자 몇 개가 떠오른다.
 * transform과 opacity만 쓴다(레이아웃 재계산 없음 = 합성 단계에서만 처리된다).
 *
 * 화면 밖 카드는 IntersectionObserver로 아예 렌더하지 않는다.
 * 목록에 카드가 수십 장 깔려도 보이는 것만 움직인다.
 */

// 카테고리 색을 모를 때(시리즈 API가 아직 color를 안 준다) 쓰는 거의 무채색 빛.
// 색을 찍으면 표지 색과 어긋날 수 있어서, 모를 때는 그냥 밝기만 더한다.
const FALLBACK = '#dfe6ff'

export default function CoverMotion({ color, className = '' }) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el || typeof IntersectionObserver === 'undefined') {
      setVisible(true)
      return undefined
    }
    const io = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin: '120px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  const c = color || FALLBACK

  return (
    <div
      ref={ref}
      aria-hidden="true"
      className={`cover-motion ${className}`}
      style={{ '--cm-accent': c }}
    >
      {visible && (
        <>
          <span className="cover-motion__glow cover-motion__glow--a" />
          <span className="cover-motion__glow cover-motion__glow--b" />
          <span className="cover-motion__dust" />
        </>
      )}
    </div>
  )
}
