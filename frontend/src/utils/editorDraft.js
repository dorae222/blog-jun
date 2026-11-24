/**
 * 글 편집기의 로컬 임시저장(localStorage).
 * 키: `editor-draft:<slug>` (아직 서버에 없는 새 글은 `editor-draft:new`).
 * 저장 실패(사생활 보호 모드, 용량 초과)는 조용히 무시한다. 서버 저장이 본 저장이고 이건 보험이다.
 */
const PREFIX = 'editor-draft:'

export function readDraft(key) {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    if (!raw) return null
    const d = JSON.parse(raw)
    return d && d.form ? d : null
  } catch {
    return null
  }
}

export function writeDraft(key, form) {
  try {
    const savedAt = Date.now()
    localStorage.setItem(PREFIX + key, JSON.stringify({ form, savedAt }))
    return savedAt
  } catch {
    return null
  }
}

export function clearDraft(key) {
  try { localStorage.removeItem(PREFIX + key) } catch { /* 무시 */ }
}

/** 대시보드 "이어 쓰기"에 보여 줄 로컬 임시본 목록(최근 순). */
export function listDrafts() {
  const out = []
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (!k?.startsWith(PREFIX)) continue
      const d = readDraft(k.slice(PREFIX.length))
      if (d) out.push({ key: k.slice(PREFIX.length), ...d })
    }
  } catch { /* 무시 */ }
  return out.sort((a, b) => b.savedAt - a.savedAt)
}
