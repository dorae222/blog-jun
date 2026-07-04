export default function TagsTab({
  tags, mergeSrc, setMergeSrc, mergeDst, setMergeDst,
  handleMerge, handleCleanup,
}) {
  return (
    <div className="space-y-6">
      {/* 병합 */}
      <div className="p-4 rounded-xl border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
        <h3 className="font-semibold mb-3" style={{ color: 'var(--text)' }}>태그 병합</h3>
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="min-w-0 sm:min-w-[12rem]">
            <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>소스 태그 (삭제됨)</label>
            <select
              value={mergeSrc}
              onChange={e => setMergeSrc(e.target.value)}
              className="w-full border rounded px-2 py-1 text-sm"
              style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
            >
              <option value="">선택</option>
              {tags.map(t => <option key={t.slug} value={t.slug}>{t.name} ({t.post_count})</option>)}
            </select>
          </div>
          <span className="hidden sm:inline text-gray-400">&rarr;</span>
          <div className="min-w-0 sm:min-w-[12rem]">
            <label className="block text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>대상 태그 (유지됨)</label>
            <select
              value={mergeDst}
              onChange={e => setMergeDst(e.target.value)}
              className="w-full border rounded px-2 py-1 text-sm"
              style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
            >
              <option value="">선택</option>
              {tags.map(t => <option key={t.slug} value={t.slug}>{t.name} ({t.post_count})</option>)}
            </select>
          </div>
          <button
            onClick={handleMerge}
            className="px-4 py-1.5 rounded bg-primary-600 text-white text-sm hover:bg-primary-700"
          >
            병합
          </button>
        </div>
      </div>

      {/* 고아 태그 삭제 */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
        <button
          onClick={handleCleanup}
          className="px-4 py-2 rounded border text-sm text-red-600 hover:bg-red-50"
          style={{ borderColor: 'var(--border)' }}
        >
          고아 태그 일괄 삭제
        </button>
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          포스트 0개인 태그를 모두 제거합니다.
        </span>
      </div>

      {/* 태그 목록 */}
      <div className="sm:hidden space-y-2">
        {tags.length === 0 && (
          <div className="px-4 py-8 rounded-xl border text-center text-sm"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', color: 'var(--text-secondary)' }}>
            태그가 없습니다.
          </div>
        )}
        {tags.map(tag => (
          <div key={tag.slug} className="rounded-xl border p-3"
            style={{ borderColor: 'var(--border)', background: 'var(--card-bg)', opacity: tag.post_count === 0 ? 0.55 : 1 }}>
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="inline-flex items-center gap-1.5 text-sm font-medium"
                  style={{ color: 'var(--text)' }}>
                  <span className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: `hsl(${(tag.name.charCodeAt(0) * 37) % 360},55%,60%)` }} />
                  <span className="truncate">{tag.name}</span>
                </p>
                <p className="mt-1 text-xs font-mono truncate" style={{ color: 'var(--text-secondary)' }}>{tag.slug}</p>
              </div>
              <span className="shrink-0 text-sm font-semibold" style={{ color: tag.post_count === 0 ? 'var(--text-secondary)' : 'var(--text)' }}>
                {tag.post_count}
              </span>
            </div>
          </div>
        ))}
      </div>
      <div className="hidden sm:block rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>태그</th>
              <th className="px-4 py-2 text-left font-medium" style={{ color: 'var(--text-secondary)' }}>슬러그</th>
              <th className="px-4 py-2 text-right font-medium" style={{ color: 'var(--text-secondary)' }}>포스트 수</th>
            </tr>
          </thead>
          <tbody>
            {tags.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                  태그가 없습니다.
                </td>
              </tr>
            )}
            {tags.map(tag => (
              <tr key={tag.slug} className="border-t"
                style={{ borderColor: 'var(--border)', opacity: tag.post_count === 0 ? 0.45 : 1 }}>
                <td className="px-4 py-2">
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium"
                    style={{ color: 'var(--text)' }}>
                    <span className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ background: `hsl(${(tag.name.charCodeAt(0) * 37) % 360},55%,60%)` }} />
                    {tag.name}
                  </span>
                </td>
                <td className="px-4 py-2 text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{tag.slug}</td>
                <td className="px-4 py-2 text-right" style={{ color: tag.post_count === 0 ? 'var(--text-secondary)' : 'var(--text)' }}>
                  {tag.post_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
