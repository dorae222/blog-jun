import {
  Cloud, Brain, Database, Code2, BookOpen, Folder, Inbox,
  Zap, Sparkles, Eye, Layers, Bot, Wrench,
} from 'lucide-react'

const MAP = {
  cloud: Cloud,
  ai: Brain,
  'ai-ml': Brain,
  data: Database,
  dev: Code2,
  foundation: BookOpen,
  program: Code2,
  inbox: Inbox,
  // AI 서브카테고리
  llm: Brain,
  ssm: Zap,
  diffusion: Sparkles,
  vision: Eye,
  multimodal: Layers,
  agent: Bot,
  technique: Wrench,
}

export function getCategoryIcon(slug, size = 16) {
  const key = slug?.toLowerCase().replace(/^[\d]+\.?\s*/, '')
  const Icon = MAP[key] || Folder
  return <Icon size={size} />
}
