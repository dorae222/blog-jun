import { Github, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t py-8 mt-16" style={{ borderColor: 'var(--border)' }}>
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          &copy; {new Date().getFullYear()} blog-jun. Built with Django + React.
        </p>
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/dorae222"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
            aria-label="GitHub"
          >
            <Github size={20} />
          </a>
          <a
            href="mailto:admin@blog.dorae222.com"
            className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
            aria-label="Email"
          >
            <Mail size={20} />
          </a>
        </div>
      </div>
    </footer>
  )
}
