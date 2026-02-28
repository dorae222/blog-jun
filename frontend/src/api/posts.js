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
