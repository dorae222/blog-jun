export function isNew(item) {
  const date = item.published_at || item.created_at
  if (!date) return false
  return Date.now() - new Date(date).getTime() < 7 * 24 * 60 * 60 * 1000
}
