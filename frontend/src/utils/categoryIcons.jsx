import { Cloud, Brain, Database, Code2, BookOpen, Folder, Inbox } from 'lucide-react'

const MAP = {
  cloud: Cloud,
  ai: Brain,
  data: Database,
  dev: Code2,
  foundation: BookOpen,
  program: Code2,
  inbox: Inbox,
}

export function getCategoryIcon(slug, size = 16) {
  const key = slug?.toLowerCase().replace(/^[\d]+\.?\s*/, '')
  const Icon = MAP[key] || Folder
  return <Icon size={size} />
}
