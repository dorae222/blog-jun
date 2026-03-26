import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-[60vh] px-4">
          <div className="text-center p-8 rounded-2xl border max-w-md"
            style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
            <AlertTriangle size={40} className="mx-auto mb-4" style={{ color: 'var(--text-secondary)' }} />
            <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
              문제가 발생했습니다
            </h2>
            <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
              페이지를 다시 로드해 주세요.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2 rounded-lg text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 transition-colors"
            >
              새로고침
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
