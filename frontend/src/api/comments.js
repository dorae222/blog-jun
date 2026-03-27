import client from './client'

export const getComments = (postSlug) =>
  client.get(`/posts/${postSlug}/comments/`)

export const createComment = (postSlug, data) =>
  client.post(`/posts/${postSlug}/comments/`, data)

export const updateComment = (id, data) =>
  client.patch(`/comments/${id}/`, data)

export const deleteComment = (id) =>
  client.delete(`/comments/${id}/`)

// 관리자 전용
export const getAdminComments = (params) =>
  client.get('/admin/comments/', { params })

export const getAdminCommentStats = () =>
  client.get('/admin/comments/stats/')

export const bulkDeleteComments = (ids) =>
  client.delete('/admin/comments/bulk-delete/', { data: { ids } })
