import { useEditor, EditorContent } from '@tiptap/react'
import { BubbleMenu } from '@tiptap/extension-bubble-menu'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'
import Underline from '@tiptap/extension-underline'
import Highlight from '@tiptap/extension-highlight'
import Typography from '@tiptap/extension-typography'
import TextAlign from '@tiptap/extension-text-align'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { TextStyle } from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import { Markdown } from 'tiptap-markdown'
import { common, createLowlight } from 'lowlight'
import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import SlashCommandMenu from './SlashCommandMenu'
import EditorToolbar from './EditorToolbar'
import EmbedBlock, { parseVideoUrl } from './EmbedBlock'
import { uploadImage } from '../../api/posts'
import './editor-styles.css'

const lowlight = createLowlight(common)

export default function NotionEditor({ content, onChange, onImageUpload }) {
  const [slashMenu, setSlashMenu] = useState(null) // { x, y, query }
  const [showVideoEmbed, setShowVideoEmbed] = useState(false)
  const slashStartPos = useRef(null)
  const imageInputRef = useRef(null)

  // 이미지 업로드 핸들러 (외부 prop 또는 기본 API 호출)
  const handleImageUpload = useCallback(async (file) => {
    if (onImageUpload) {
      return await onImageUpload(file)
    }
    // 기본: API를 통해 업로드
    const formData = new FormData()
    formData.append('image', file)
    const { data } = await uploadImage(formData)
    return data.image
  }, [onImageUpload])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false, // CodeBlockLowlight로 대체
      }),
      Placeholder.configure({
        placeholder: "Type '/' for commands...",
      }),
      Image.configure({
        inline: false,
        allowBase64: true,
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
      }),
      TaskList,
      TaskItem.configure({
        nested: true,
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      Underline,
      Highlight.configure({
        multicolor: true,
      }),
      Typography,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Superscript,
      Subscript,
      CodeBlockLowlight.configure({
        lowlight,
      }),
      TextStyle,
      Color,
      Markdown.configure({
        html: true,
        tightLists: true,
        bulletListMarker: '-',
        transformPastedText: true,
        transformCopiedText: true,
      }),
    ],
    content: content || '',
    editorProps: {
      attributes: {
        class: 'notion-editor-content',
      },
      // 클립보드 붙여넣기 핸들링
      handlePaste: (view, event) => {
        // 이미지 파일 붙여넣기
        const files = event.clipboardData?.files
        if (files && files.length > 0) {
          const imageFile = Array.from(files).find(f => f.type.startsWith('image/'))
          if (imageFile) {
            event.preventDefault()
            handleImageUpload(imageFile)
              .then(url => {
                editor.chain().focus().setImage({ src: url, alt: imageFile.name }).run()
                toast.success('Image uploaded!')
              })
              .catch(() => toast.error('Image upload failed'))
            return true
          }
        }

        // YouTube/Vimeo URL 자동 임베드
        const text = event.clipboardData?.getData('text/plain')
        if (text) {
          const parsed = parseVideoUrl(text.trim())
          if (parsed) {
            event.preventDefault()
            const iframeHtml = `<div class="video-embed"><iframe src="${parsed.embedUrl}" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;border-radius:8px;"></iframe></div><p></p>`
            editor.chain().focus().insertContent(iframeHtml).run()
            return true
          }
        }

        return false
      },
      // 드래그 앤 드롭 이미지
      handleDrop: (view, event) => {
        const files = event.dataTransfer?.files
        if (files && files.length > 0) {
          const imageFile = Array.from(files).find(f => f.type.startsWith('image/'))
          if (imageFile) {
            event.preventDefault()
            handleImageUpload(imageFile)
              .then(url => {
                const pos = view.posAtCoords({ left: event.clientX, top: event.clientY })
                if (pos) {
                  editor.chain().focus().setImage({ src: url, alt: imageFile.name }).run()
                }
                toast.success('Image uploaded!')
              })
              .catch(() => toast.error('Image upload failed'))
            return true
          }
        }
        return false
      },
    },
    onUpdate: ({ editor }) => {
      // Markdown으로 변환하여 부모에게 전달
      const markdown = editor.storage.markdown.getMarkdown()
      onChange?.(markdown)
    },
  })

  // "/" 슬래시 커맨드 감지
  useEffect(() => {
    if (!editor) return

    const handleTransaction = () => {
      const { state } = editor
      const { $from } = state.selection

      // 현재 커서 위치의 텍스트 노드에서 "/" 감지
      const textBefore = $from.parent.textContent.slice(0, $from.parentOffset)

      // "/" 으로 시작하는 패턴 감지 (줄 시작 또는 공백 뒤)
      const slashMatch = textBefore.match(/(?:^|\s)\/([\w가-힣]*)$/)

      if (slashMatch) {
        const query = slashMatch[1] || ''
        // 에디터 뷰에서 커서 위치 가져오기
        const coords = editor.view.coordsAtPos($from.pos)
        const editorRect = editor.view.dom.getBoundingClientRect()

        setSlashMenu({
          x: coords.left - editorRect.left,
          y: coords.bottom - editorRect.top + 4,
          query,
        })
        slashStartPos.current = $from.pos - slashMatch[0].trimStart().length
      } else if (slashMenu) {
        setSlashMenu(null)
        slashStartPos.current = null
      }
    }

    editor.on('transaction', handleTransaction)
    return () => editor.off('transaction', handleTransaction)
  }, [editor, slashMenu])

  // 슬래시 커맨드 아이템 선택
  const handleSlashSelect = useCallback((item) => {
    if (!editor || slashStartPos.current === null) return

    // "/" 텍스트 삭제
    const { state } = editor
    const from = slashStartPos.current
    const to = state.selection.$from.pos

    editor.chain()
      .focus()
      .deleteRange({ from, to })
      .run()

    // 특수 커맨드 처리
    if (item.id === 'image') {
      imageInputRef.current?.click()
    } else if (item.id === 'video') {
      setShowVideoEmbed(true)
    } else if (item.id === 'math') {
      // KaTeX 수식 블록 (코드블록으로 대체하여 markdown에서 $$...$$ 형태로)
      editor.chain().focus().insertContent('$$\n\n$$').run()
    } else if (item.command) {
      item.command(editor)
    }

    setSlashMenu(null)
    slashStartPos.current = null
  }, [editor])

  // 이미지 파일 선택 핸들러
  const handleImageFileSelect = useCallback(async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const url = await handleImageUpload(file)
      editor?.chain().focus().setImage({ src: url, alt: file.name }).run()
      toast.success('Image uploaded!')
    } catch {
      toast.error('Image upload failed')
    }
    // input 초기화
    if (imageInputRef.current) imageInputRef.current.value = ''
  }, [editor, handleImageUpload])

  // 비디오 임베드 핸들러
  const handleVideoEmbed = useCallback((videoInfo) => {
    if (!editor) return
    const iframeHtml = `<div class="video-embed"><iframe src="${videoInfo.embedUrl}" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;border-radius:8px;"></iframe></div><p></p>`
    editor.chain().focus().insertContent(iframeHtml).run()
    setShowVideoEmbed(false)
  }, [editor])

  if (!editor) return null

  return (
    <div className="notion-editor relative flex-1 flex flex-col overflow-hidden">
      {/* BubbleMenu: 텍스트 선택 시 나타나는 플로팅 툴바 */}
      <BubbleMenu
        editor={editor}
        tippyOptions={{ duration: 150, placement: 'top' }}
        className="bubble-menu"
      >
        <EditorToolbar editor={editor} />
      </BubbleMenu>

      {/* 에디터 본문 */}
      <div className="flex-1 overflow-y-auto relative">
        <EditorContent editor={editor} className="notion-editor-wrapper" />

        {/* Slash Command Menu */}
        {slashMenu && (
          <div
            className="absolute z-50"
            style={{
              left: `${slashMenu.x}px`,
              top: `${slashMenu.y}px`,
            }}
          >
            <SlashCommandMenu
              editor={editor}
              query={slashMenu.query}
              onSelect={handleSlashSelect}
              onClose={() => {
                setSlashMenu(null)
                slashStartPos.current = null
              }}
            />
          </div>
        )}
      </div>

      {/* 비디오 임베드 UI */}
      {showVideoEmbed && (
        <div className="absolute bottom-4 left-4 right-4 z-40">
          <EmbedBlock
            onEmbed={handleVideoEmbed}
            onClose={() => setShowVideoEmbed(false)}
          />
        </div>
      )}

      {/* 숨겨진 이미지 파일 input */}
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleImageFileSelect}
      />
    </div>
  )
}
