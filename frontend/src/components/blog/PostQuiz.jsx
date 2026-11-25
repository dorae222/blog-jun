import { ChevronRight } from 'lucide-react'

/**
 * 글 끝 확인 질문. 답은 접혀 있다가 누르면 펼쳐진다.
 * <details>/<summary> 라서 Tab 으로 옮기고 Enter·Space 로 여닫을 수 있다. quiz 가 없으면 아무것도 그리지 않는다.
 */
export default function PostQuiz({ quiz }) {
  const items = (quiz || []).filter((x) => x?.q && x?.a)
  if (!items.length) return null

  return (
    <section className="not-prose mt-10 border-t pt-8" style={{ borderColor: 'var(--border)' }} aria-label="읽고 나서 확인하기">
      <p className="m-0 text-lg font-bold" style={{ color: 'var(--text)' }}>읽고 나서 확인하기</p>
      <p className="m-0 mt-1 mb-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
        먼저 답을 떠올려 본 다음 질문을 눌러 맞춰 보세요.
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
                <span className="min-w-0 flex-1 break-words">{item.q}</span>
                <span className="shrink-0 text-xs font-normal group-open:hidden" style={{ color: 'var(--text-secondary)' }}>답 보기</span>
              </summary>
              <div className="border-t px-4 py-3" style={{ borderColor: 'var(--border)' }}>
                <p className="m-0 whitespace-pre-line text-[0.95rem] leading-relaxed break-words" style={{ color: 'var(--text)' }}>{item.a}</p>
                {item.where && (
                  <p className="m-0 mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                    어디에 나오나: {item.where}
                  </p>
                )}
              </div>
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}
