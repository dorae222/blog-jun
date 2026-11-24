import client from './client'

/**
 * 개인 메모(staff 전용). blog-api `/api/notes/` 계약:
 * 목록은 DRF 페이지네이션 형식 {count, next, previous, results}.
 */
export const getNotes = (params) => client.get('/notes/', { params })
export const getNote = (id) => client.get(`/notes/${id}/`)
export const createNote = (data) => client.post('/notes/', data)
export const updateNote = (id, data) => client.patch(`/notes/${id}/`, data)
export const deleteNote = (id) => client.delete(`/notes/${id}/`)
export const getNoteTags = () => client.get('/notes/tags/')
export const convertNoteToPost = (id) => client.post(`/notes/${id}/convert-to-post/`)

/** 메모 색상 팔레트. 값은 서버에 그대로 저장되는 키다(빈 문자열 = 기본). */
export const NOTE_COLORS = [
  { key: '', label: '기본', swatch: 'var(--card-bg)' },
  { key: 'yellow', label: '노랑', swatch: '#fef3c7' },
  { key: 'green', label: '초록', swatch: '#dcfce7' },
  { key: 'blue', label: '파랑', swatch: '#dbeafe' },
  { key: 'purple', label: '보라', swatch: '#ede9fe' },
  { key: 'pink', label: '분홍', swatch: '#fce7f3' },
  { key: 'gray', label: '회색', swatch: '#f1f5f9' },
]

export const noteSwatch = (key) => NOTE_COLORS.find((c) => c.key === (key || ''))?.swatch || 'var(--card-bg)'
