export default function Footer() {
  return (
    <footer className="border-t py-8 mt-16" style={{ borderColor: 'var(--border)' }}>
      <div className="max-w-6xl mx-auto px-4 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
        <p>&copy; {new Date().getFullYear()} blog-jun. Built with Django + React.</p>
        <div className="mt-2 flex justify-center gap-4">
          <a href="https://github.com/dorae222" target="_blank" rel="noopener noreferrer" className="hover:text-primary-600 transition-colors">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  )
}
