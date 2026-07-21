import { CARD_COLORS } from '../../data/cardColors'

/**
 * AuroraBackground — 화이트 무드 위에 은은하게 흐르는 라이트 그라디언트 메시.
 * blur된 큰 blob 3개가 카드 팔레트 색(저채도·저opacity)으로 아주 느리게 이동한다.
 * 하드코딩 hex 없음(CARD_COLORS.rgb 사용), prefers-reduced-motion이면 CSS에서 정지.
 */
const BLOBS = [
  { rgb: CARD_COLORS.blue.rgb,   opacity: 0.14, size: 46, top: '-10%', left: '-8%',  anim: 'aurora-1 34s ease-in-out infinite' },
  { rgb: CARD_COLORS.purple.rgb, opacity: 0.12, size: 42, top: '12%',  left: '58%',  anim: 'aurora-2 42s ease-in-out infinite' },
  { rgb: CARD_COLORS.cyan.rgb,   opacity: 0.10, size: 40, top: '52%',  left: '8%',   anim: 'aurora-3 48s ease-in-out infinite' },
]

export default function AuroraBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {BLOBS.map((b, i) => (
        <div
          key={i}
          className="aurora-blob absolute rounded-full"
          style={{
            width: `${b.size}rem`,
            height: `${b.size}rem`,
            top: b.top,
            left: b.left,
            background: `radial-gradient(circle at center, rgba(${b.rgb}, ${b.opacity}) 0%, rgba(${b.rgb}, 0) 70%)`,
            filter: 'blur(44px)',
            animation: b.anim,
          }}
        />
      ))}
    </div>
  )
}
