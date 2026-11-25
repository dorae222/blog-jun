// 글 첨부 파일(실습 파일)과 본문 링크 판별. 화면 없이 쓸 수 있는 순수 함수만 둔다(npm test).

export const ATTACHMENT_KINDS = ['xlsx', 'ipynb', 'csv', 'pdf', 'zip', 'py']
export const ATTACHMENT_ACCEPT = ATTACHMENT_KINDS.map((k) => `.${k}`).join(',')
export const ATTACHMENT_MAX_BYTES = 20 * 1024 * 1024

export const KIND_LABEL = {
  xlsx: '엑셀',
  ipynb: '노트북',
  csv: 'CSV',
  pdf: 'PDF',
  zip: '압축 파일',
  py: '파이썬',
}

const OWN_HOSTS = ['blog.dorae222.com', 'k8s-blog.dorae222.com']

export function formatBytes(n) {
  if (!Number.isFinite(n) || n < 0) return ''
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(n < 10 * 1024 ? 1 : 0)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function kindFromName(name) {
  const m = /\.([a-z0-9]+)$/i.exec(name || '')
  const ext = m ? m[1].toLowerCase() : ''
  return ATTACHMENT_KINDS.includes(ext) ? ext : ''
}

/**
 * 본문 링크가 첨부 파일(/media/.../files/<이름>)이면 그 경로를, 아니면 null 을 돌려준다.
 * 다른 사이트의 링크는 주소가 비슷해도 첨부로 보지 않는다.
 */
export function attachmentPath(href, currentHost = '') {
  if (typeof href !== 'string' || !href) return null
  let path = href
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//')) {
    let u
    try { u = new URL(href, 'https://blog.dorae222.com') } catch { return null }
    if (!/^https?:$/.test(u.protocol)) return null
    if (!OWN_HOSTS.includes(u.hostname) && u.hostname !== currentHost) return null
    path = u.pathname
  }
  path = path.split(/[?#]/)[0]
  if (path.includes('..')) return null
  return /^\/media\/(?:[^/]+\/)+files\/[^/]+$/.test(path) ? path : null
}

export function filenameFromPath(path) {
  const last = (path || '').split('/').pop() || ''
  try { return decodeURIComponent(last) } catch { return last }
}

/** 본문 링크 하나를 AttachmentList 가 그릴 수 있는 항목으로 바꾼다. 글의 첨부 목록에 있으면 그 정보를 쓴다. */
export function attachmentFromLink(path, text, attachments = []) {
  const known = attachments.find((a) => a.url === path || filenameFromPath(a.url) === filenameFromPath(path))
  if (known) return known
  const filename = filenameFromPath(path)
  const label = (text || '').trim()
  return {
    id: path,
    filename,
    url: path,
    size_bytes: null,
    kind: kindFromName(filename),
    description: label && label !== filename && label !== path ? label : '',
  }
}
