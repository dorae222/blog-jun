import client from './client'

export const getPosts = (params) => client.get('/posts/', { params })
export const getPost = (slug) => client.get(`/posts/${slug}/`)
export const createPost = (data) => client.post('/posts/', data)
export const updatePost = (slug, data) => client.patch(`/posts/${slug}/`, data)
export const deletePost = (slug) => client.delete(`/posts/${slug}/`)
export const searchPosts = (q) => client.get('/posts/search/', { params: { q } })

export const getCategories = () => client.get('/categories/')
export const getTags = () => client.get('/tags/')
// 편집기 태그 자동완성용: 기본 페이지(12개)에서 잘리지 않게 전부 받는다(서버 상한 1000).
export const getAllTags = () => client.get('/tags/', { params: { page_size: 1000 } })
export const createTag = (data) => client.post('/tags/', data)
// 시리즈가 120개를 넘어서 page_size 100이면 뒤쪽이 통째로 잘렸다.
// 홈에서 순서를 섞으려면 목록 전체가 손에 있어야 한다.
export const getSeries = (params) => client.get('/series/', { params: { page_size: 300, ...params } })
export const getSeriesDetail = (slug) => client.get(`/series/${slug}/`)
export const getTemplates = () => client.get('/templates/')

export const uploadImage = (formData) =>
  client.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

// 글 첨부 파일(실습 파일). 올리기는 20MB 까지라 기본 30초 제한을 늘린다.
export const getAttachments = (slug) => client.get(`/posts/${slug}/attachments/`)
export const uploadAttachment = (slug, formData, onUploadProgress) =>
  client.post(`/posts/${slug}/attachments/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
    onUploadProgress,
  })
export const updateAttachment = (slug, id, data) => client.patch(`/posts/${slug}/attachments/${id}/`, data)
export const deleteAttachment = (slug, id) => client.delete(`/posts/${slug}/attachments/${id}/`)

export const getStats = () => client.get('/stats/')
export const getDashboardStats = () => client.get('/dashboard/stats/')

export const bulkDeletePosts = (slugs) => client.post('/posts/bulk_delete/', { slugs })
export const bulkUpdateStatus = (slugs, status) => client.post('/posts/bulk_update_status/', { slugs, status })
export const getAuditResults = () => client.get('/audit/results/')
export const mergeTags = (source, target) => client.post('/tags/merge/', { source, target })
export const cleanupTags = () => client.post('/tags/cleanup/')

// Feed API (통합 피드)
export const getFeed = (params) => client.get('/feed/', { params })
export const getPopularPosts = (limit = 5) => client.get('/feed/popular/', { params: { limit } })

// Architecture API
export const getArchitectures = (params) => client.get('/architectures/', { params })
export const getArchitecture = (slug) => client.get(`/architectures/${slug}/`)
export const createArchitecture = (data) => client.post('/architectures/', data)
export const updateArchitecture = (slug, data) => client.patch(`/architectures/${slug}/`, data)
export const deleteArchitecture = (slug) => client.delete(`/architectures/${slug}/`)
export const getArchitectureConcepts = () => client.get('/architectures/concepts/')
export const getArchitectureStats = () => client.get('/architectures/stats/')
export const getArchitectureTree = (params) => client.get('/architectures/tree/', { params })
export const updateArchitecturePosition = (slug, x, y) =>
  client.post(`/architectures/${slug}/update_position/`, { x, y })
export const createArchitectureRelation = (data) =>
  client.post('/architectures/relations/', data)
export const deleteArchitectureRelation = (fromSlug, toSlug) =>
  client.delete('/architectures/relations/', { data: { from_slug: fromSlug, to_slug: toSlug } })
export const uploadArchitectureFigure = (slug, formData) =>
  client.post(`/architectures/${slug}/upload_figure/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

// Cloud Service API
export const getCloudServiceTree = (params) => client.get('/cloud-services/tree/', { params })
export const updateCloudServicePosition = (slug, x, y) =>
  client.post(`/cloud-services/${slug}/update_position/`, { x, y })
export const createCloudServiceRelation = (data) =>
  client.post('/cloud-services/relations/', data)
export const deleteCloudServiceRelation = (fromSlug, toSlug) =>
  client.delete('/cloud-services/relations/', { data: { from_slug: fromSlug, to_slug: toSlug } })

// Cover Image API
export const generateCover = (slug) => client.post(`/posts/${slug}/generate_cover/`)
export const getCoverTemplates = () => client.get('/cover-templates/')
