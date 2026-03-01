import { useState, useRef, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

export default function PDFViewer({ url, title }) {
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [isLandscape, setIsLandscape] = useState(false)
  const containerRef = useRef(null)

  const onDocumentLoadSuccess = useCallback(({ numPages }) => {
    setNumPages(numPages)
    setPageNumber(1)
  }, [])

  const onPageLoadSuccess = useCallback((page) => {
    const { width, height } = page.getViewport({ scale: 1 })
    setIsLandscape(width > height)
  }, [])

  const containerWidth = containerRef.current?.clientWidth || 700
  const pageWidth = isLandscape ? containerWidth : Math.min(containerWidth * 0.75, 600)

  return (
    <div
      ref={containerRef}
      className="my-6 border rounded-lg overflow-hidden"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
    >
      {/* 헤더 */}
      <div
        className="flex items-center justify-between px-4 py-2 border-b"
        style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
      >
        <span className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
          {title}
        </span>
        <a
          href={url}
          download
          className="text-xs shrink-0 ml-4 hover:underline"
          style={{ color: 'var(--text-secondary)' }}
        >
          다운로드
        </a>
      </div>

      {/* PDF 렌더링 */}
      <div className="flex flex-col items-center py-4 px-2">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div
              className="h-64 animate-pulse rounded w-full"
              style={{ background: 'var(--border)' }}
            />
          }
          error={
            <div className="py-8 text-sm text-center" style={{ color: 'var(--text-secondary)' }}>
              PDF를 불러올 수 없습니다.{' '}
              <a href={url} className="hover:underline" style={{ color: 'var(--text)' }}>
                직접 열기
              </a>
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            width={pageWidth}
            onLoadSuccess={onPageLoadSuccess}
            renderTextLayer
            renderAnnotationLayer
          />
        </Document>
      </div>

      {/* 페이지 네비게이션 */}
      {numPages > 1 && (
        <div
          className="flex items-center justify-center gap-4 py-2 border-t"
          style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}
        >
          <button
            onClick={() => setPageNumber((p) => Math.max(p - 1, 1))}
            disabled={pageNumber <= 1}
            className="px-3 py-1 text-sm rounded transition-opacity disabled:opacity-40"
            style={{ color: 'var(--text)' }}
          >
            이전
          </button>
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {pageNumber} / {numPages}
          </span>
          <button
            onClick={() => setPageNumber((p) => Math.min(p + 1, numPages))}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 text-sm rounded transition-opacity disabled:opacity-40"
            style={{ color: 'var(--text)' }}
          >
            다음
          </button>
        </div>
      )}
    </div>
  )
}
