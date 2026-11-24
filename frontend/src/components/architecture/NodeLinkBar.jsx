import { useNavigate } from 'react-router-dom'
import { ExternalLink, ArrowRight, FileX } from 'lucide-react'

// 선택한 노드의 링크 두 개를 그래프 하단 가운데에 띄운다.
//
// 왜 패널이 아니라 여기인가. 상세 패널은 오른쪽 끝에 붙어 있어서 그래프를 보다가
// 눈을 크게 옮겨야 닿는다. 범례가 앉은 하단 줄에 나란히 두면 시선 안에 들어온다.
// 노드를 고르지 않았으면 아무것도 그리지 않는다.
//
// 두 링크는 성격이 다르므로 형태로 가른다.
//   논문 원문  밖으로 나가는 링크. 테두리 스타일 + 바깥 화살표
//   해설 글    이 사이트 안 이동. 채운 스타일 + 오른쪽 화살표
// 링크가 없으면 지우지 않고 비활성으로 남긴다. 논문이 원래 없는 항목이라는 것도 정보다.
export default function NodeLinkBar({ node }) {
  const navigate = useNavigate()
  if (!node) return null

  const base =
    'inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-semibold whitespace-nowrap'

  // 좁은 화면에서는 상세 패널이 하단 시트로 바뀌어 이 자리를 덮는다.
  // 그쪽에도 같은 링크가 있으므로 `hidden md:flex`로 여기서는 숨긴다.
  return (
    <div
      className="hidden md:flex absolute bottom-3 left-1/2 -translate-x-1/2 z-20 items-center gap-2 rounded-xl px-2 py-2"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
        opacity: 0.96,
        backdropFilter: 'blur(8px)',
        maxWidth: 'calc(100% - 24px)',
      }}
    >
      {/* 어느 노드의 링크인지 밝힌다. 그래프에는 노드가 200개가 넘어서
          이름이 없으면 무엇을 여는 버튼인지 알 수 없다 */}
      <span
        className="px-1.5 text-xs font-semibold truncate"
        style={{ color: 'var(--text-secondary)', maxWidth: 160 }}
        title={node.name}
      >
        {node.name}
      </span>

      {node.paper_url ? (
        <a
          href={node.paper_url}
          target="_blank"
          rel="noopener noreferrer"
          className={`${base} transition-all hover:-translate-y-0.5 hover:shadow-md
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400`}
          style={{ border: '1.5px solid var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
          title="논문 원문을 새 탭에서 연다"
        >
          논문 원문 <ExternalLink size={14} />
        </a>
      ) : (
        <span
          className={`${base} cursor-not-allowed select-none`}
          style={{ border: '1px dashed var(--border)', color: 'var(--text-secondary)', opacity: 0.7 }}
          aria-disabled="true"
          title="공개된 논문이 없는 항목이다"
        >
          <FileX size={14} /> 논문 없음
        </span>
      )}

      {node.related_post_slug ? (
        <button
          onClick={() => navigate(`/post/${node.related_post_slug}`)}
          className={`${base} bg-primary-600 text-white transition-all
            hover:bg-primary-700 hover:shadow-lg hover:-translate-y-0.5
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400`}
          style={{ border: '1px solid var(--color-primary-700)', boxShadow: '0 1px 3px rgba(37,99,235,0.35)' }}
          title="이 사이트의 해설 글로 이동한다"
        >
          컨텐츠 보러가기 <ArrowRight size={14} />
        </button>
      ) : (
        <span
          className={`${base} cursor-not-allowed select-none`}
          style={{ border: '1px dashed var(--border)', color: 'var(--text-secondary)', opacity: 0.7 }}
          aria-disabled="true"
          title="아직 해설 글이 없는 항목이다"
        >
          <FileX size={14} /> 컨텐츠 없음
        </span>
      )}
    </div>
  )
}
