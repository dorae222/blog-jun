import client from './client'

export const getPosts = (params) => client.get('/posts/', { params })
export const getPost = (slug) => client.get(`/posts/${slug}/`)
export const createPost = (data) => client.post('/posts/', data)
export const updatePost = (slug, data) => client.patch(`/posts/${slug}/`, data)
export const deletePost = (slug) => client.delete(`/posts/${slug}/`)
export const searchPosts = (q) => client.get('/posts/search/', { params: { q } })

export const getCategories = () => client.get('/categories/')
export const getTags = () => client.get('/tags/')
export const getSeries = () => client.get('/series/')
export const getSeriesDetail = (slug) => client.get(`/series/${slug}/`)
export const getTemplates = () => client.get('/templates/')

export const uploadImage = (formData) =>
  client.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

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
export const getArchitectureTree = () => client.get('/architectures/tree/')
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

// Cover Image API
export const generateCover = (slug) => client.post(`/posts/${slug}/generate_cover/`)
export const getCoverTemplates = () => client.get('/cover-templates/')
