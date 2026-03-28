import {
  Cloud, Brain, Database, Code2, BookOpen, Folder, Inbox,
  Zap, Sparkles, Eye, Layers, Bot, Wrench, Terminal,
  Gauge, Lightbulb, GraduationCap, Search, Code,
} from 'lucide-react'
import { AwsIcon, DockerIcon, LxdIcon, DevOpsIcon } from '../components/icons/CategorySvgIcons'

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
  efficiency: Gauge,
  reasoning: Lightbulb,
  training: GraduationCap,
  rag: Search,
  code: Code,
  // Tool 카테고리
  tool: Terminal,
  'claude-code': Terminal,
  'gemini-cli': Terminal,
  'codex-cli': Terminal,
  openclaw: Terminal,
  opencode: Terminal,
  // Cloud 서브카테고리
  aws: AwsIcon,
  docker: DockerIcon,
  lxd: LxdIcon,
  devops: DevOpsIcon,
}

export function getCategoryIcon(slug, size = 16) {
  const key = slug?.toLowerCase().replace(/^[\d]+\.?\s*/, '')
  const Icon = MAP[key] || Folder
  return <Icon size={size} />
}
