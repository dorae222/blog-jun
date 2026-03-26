import { Link } from 'react-router-dom'
import { Github, Mail, Linkedin } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t py-8 mt-16" style={{ borderColor: 'var(--border)' }}>
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex flex-col sm:flex-row items-center sm:justify-between gap-4">
          <div className="text-center sm:text-left">
            <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>HJ Tech Blog</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
              AI, Cloud, Data Engineering
            </p>
          </div>

          <nav className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
            <Link to="/posts" className="hover:text-primary-600 transition-colors">Posts</Link>
            <Link to="/about" className="hover:text-primary-600 transition-colors">About</Link>
          </nav>

          <div className="flex items-center gap-2">
            <a
              href="https://github.com/dorae222"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
              aria-label="GitHub"
            >
              <Github size={18} />
            </a>
            <a
              href="https://www.linkedin.com/in/hyeongjun-do-5519321aa/"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
              aria-label="LinkedIn"
            >
              <Linkedin size={18} />
            </a>
            <a
              href="mailto:dhj9842@gmail.com"
              className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
              aria-label="Email"
            >
              <Mail size={18} />
            </a>
          </div>
        </div>
        <p className="text-xs text-center mt-4" style={{ color: 'var(--text-secondary)' }}>
          &copy; {new Date().getFullYear()} Do HyeongJun
        </p>
      </div>
    </footer>
  )
}
