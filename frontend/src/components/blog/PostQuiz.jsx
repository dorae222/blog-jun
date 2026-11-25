import { ChevronRight } from 'lucide-react'
import InlineRich from '../common/InlineRich'
import { headingKey, headingSource } from '../../utils/headingText'

/**
 * 글 끝 확인 질문. 답은 접혀 있다가 누르면 펼쳐진다.
 * <details>/<summary> 라서 Tab 으로 옮기고 Enter·Space 로 여닫을 수 있다. quiz 가 없으면 아무것도 그리지 않는다.
 */
/** 답의 근거가 된 본문 소제목으로 이동한다. 제목 글자가 같은 h2~h4 를 찾아 스크롤한다. */
function goToHeading(text) {
  // 소제목에 수식이 있으면 화면 글자가 원문과 다르다. 수식을 TeX 원문으로 되돌려 비교한다.
  const want = headingKey(text)
  if (!want) return
  const hit = [...document.querySelectorAll('article h2, article h3, article h4, .prose h2, .prose h3, .prose h4')]
    .find((h) => headingKey(headingSource(h)) === want)
  if (hit) hit.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function PostQuiz({ quiz }) {
  const items = (quiz || []).filter((x) => x?.q && x?.a)
  if (!items.length) return null

  return (
    <section className="not-prose mt-10 border-t pt-8" style={{ borderColor: 'var(--border)' }} aria-label="확인 질문">
      <p className="m-0 text-lg font-bold" style={{ color: 'var(--text)' }}>확인 질문</p>
      <p className="m-0 mt-1 mb-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
        질문을 누르면 답이 펼쳐진다.
      </p>
      <ol className="m-0 list-none p-0 space-y-2">
        {items.map((item, i) => (
          <li key={i}>
            <details className="group rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
              <summary
                className="tap-target flex cursor-pointer list-none items-start gap-2.5 rounded-xl px-4 py-3 text-[0.95rem] font-medium [&::-webkit-details-marker]:hidden"
                style={{ color: 'var(--text)' }}
              >
                <ChevronRight size={18} aria-hidden="true"
                  className="mt-0.5 shrink-0 transition-transform group-open:rotate-90"
                  style={{ color: 'var(--text-secondary)' }} />
                <span className="shrink-0 tabular-nums" style={{ color: 'var(--text-secondary)' }}>Q{i + 1}.</span>
                <span className="min-w-0 flex-1 break-words"><InlineRich text={item.q} /></span>
                <span className="shrink-0 text-xs font-normal group-open:hidden" style={{ color: 'var(--text-secondary)' }}>답 보기</span>
              </summary>
              <div className="border-t px-4 py-3" style={{ borderColor: 'var(--border)' }}>
                <p className="m-0 whitespace-pre-line text-[0.95rem] leading-relaxed break-words" style={{ color: 'var(--text)' }}><InlineRich text={item.a} /></p>
                {item.where && (
                  <button type="button" onClick={() => goToHeading(item.where)}
                    className="mt-2 inline-flex items-center gap-1 text-xs text-primary-600 hover:underline">
                    <span>본문에서 다시 보기: <InlineRich text={item.where} /></span>
                  </button>
                )}
              </div>
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}
