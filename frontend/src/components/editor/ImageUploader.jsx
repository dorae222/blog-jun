import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { uploadImage } from '../../api/posts'

const IMAGE_TYPES = [
  { value: 'general', label: '일반' },
  { value: 'paper_figure', label: '논문 Figure' },
  { value: 'code_output', label: '코드 결과' },
  { value: 'diagram', label: '다이어그램' },
]

export default function ImageUploader({ onInsert }) {
  const inputRef = useRef(null)
  const [showDialog, setShowDialog] = useState(false)
  const [pending, setPending] = useState(null)
  const [caption, setCaption] = useState('')
  const [altText, setAltText] = useState('')
  const [sourceRef, setSourceRef] = useState('')
  const [imageType, setImageType] = useState('general')

  const handleUpload = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      toast.error('이미지 파일을 선택하세요')
      return
    }

    const formData = new FormData()
    formData.append('image', file)

    try {
      const { data } = await uploadImage(formData)
      setPending({ url: data.image, name: file.name })
      setAltText(file.name.replace(/\.[^.]+$/, ''))
      setCaption('')
      setSourceRef('')
      setImageType('general')
      setShowDialog(true)
    } catch {
      toast.error('업로드 실패')
    }
  }

  const handleInsert = () => {
    if (!pending) return

    let markdown = ''
    if (caption || sourceRef) {
      // <figure> + <figcaption> 형식
      markdown += `\n\n**${caption || altText}**\n\n`
      markdown += `![${altText}](${pending.url})`
      if (sourceRef) {
        markdown += `\n*출처: ${sourceRef}*`
      }
    } else {
      markdown = `![${altText}](${pending.url})`
    }

    onInsert(markdown)
    setShowDialog(false)
    setPending(null)
    toast.success('이미지 삽입됨')
  }

  const handleSkip = () => {
    if (!pending) return
    onInsert(`![${pending.name}](${pending.url})`)
    setShowDialog(false)
    setPending(null)
    toast.success('이미지 업로드됨')
  }

  return (
    <>
      <button
        onClick={() => inputRef.current?.click()}
        className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
        style={{ borderColor: 'var(--border)' }}
      >
        Upload Image
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={e => handleUpload(e.target.files[0])}
      />

      {/* 캡션 입력 다이얼로그 */}
      {showDialog && (
        <div
          className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
          onClick={() => handleSkip()}
        >
          <div
            className="w-full max-w-md rounded-2xl p-6 space-y-4"
            style={{ background: 'var(--card-bg)' }}
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold" style={{ color: 'var(--text)' }}>
              이미지 정보
            </h3>

            {pending && (
              <img
                src={pending.url}
                alt="Preview"
                className="w-full max-h-48 object-contain rounded-lg"
                style={{ background: 'var(--bg-secondary)' }}
              />
            )}

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                  Alt Text
                </label>
                <input
                  value={altText}
                  onChange={e => setAltText(e.target.value)}
                  className="w-full text-sm px-3 py-2 rounded border mt-1"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
                  placeholder="이미지 설명"
                />
              </div>

              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                  캡션 (선택)
                </label>
                <input
                  value={caption}
                  onChange={e => setCaption(e.target.value)}
                  className="w-full text-sm px-3 py-2 rounded border mt-1"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
                  placeholder="Figure 1: 아키텍처 다이어그램"
                />
              </div>

              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                  출처 (선택)
                </label>
                <input
                  value={sourceRef}
                  onChange={e => setSourceRef(e.target.value)}
                  className="w-full text-sm px-3 py-2 rounded border mt-1"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
                  placeholder="Vaswani et al. (2017), NeurIPS"
                />
              </div>

              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                  이미지 유형
                </label>
                <select
                  value={imageType}
                  onChange={e => setImageType(e.target.value)}
                  className="w-full text-sm px-3 py-2 rounded border mt-1"
                  style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
                >
                  {IMAGE_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={handleSkip}
                className="text-sm px-4 py-2 rounded border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
              >
                Skip
              </button>
              <button
                onClick={handleInsert}
                className="text-sm px-4 py-2 rounded bg-primary-600 text-white hover:bg-primary-700"
              >
                Insert
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
