import { useEditor, EditorContent } from '@tiptap/react'
import { BubbleMenu } from '@tiptap/react/menus'
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
import Mathematics from '@tiptap/extension-mathematics'
import { common, createLowlight } from 'lowlight'
import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import SlashCommandMenu from './SlashCommandMenu'
import EditorToolbar from './EditorToolbar'
import EmbedBlock, { parseVideoUrl } from './EmbedBlock'
import CodeCell from './extensions/CodeCell'
import MermaidBlock from './extensions/MermaidBlock'
import CalloutBlock from './extensions/CalloutBlock'
import { uploadImage } from '../../api/posts'
import './editor-styles.css'

const lowlight = createLowlight(common)

// .ipynb → 에디터 콘텐츠 변환
function convertNotebookToContent(notebook) {
  const cells = notebook.cells || []
  const parts = []

  for (const cell of cells) {
    const source = (cell.source || []).join('')
    if (!source.trim()) continue

    if (cell.cell_type === 'markdown') {
      parts.push(source)
    } else if (cell.cell_type === 'code') {
      // 매직 커맨드 필터링
      const cleanCode = source
        .split('\n')
        .filter(line => !line.trim().match(/^[!%]/))
        .join('\n')
        .trim()
      if (!cleanCode) continue

      parts.push('```python\n' + cleanCode + '\n```')

      // output 처리
      const outputs = cell.outputs || []
      const outputTexts = []
      for (const out of outputs) {
        if (out.text) {
          outputTexts.push((Array.isArray(out.text) ? out.text.join('') : out.text).trim())
        } else if (out.data?.['text/plain']) {
          const txt = out.data['text/plain']
          outputTexts.push((Array.isArray(txt) ? txt.join('') : txt).trim())
        }
      }
      const outputStr = outputTexts.filter(Boolean).join('\n').trim()
      // 프로그레스바/warning 클리닝
      const cleanOutput = outputStr
        .split('\n')
        .filter(line => !line.includes('━') && !line.includes('██') && !line.match(/DeprecationWarning|FutureWarning/))
        .join('\n')
        .trim()
      if (cleanOutput) {
        parts.push('<details><summary>Output</summary>\n\n```\n' + cleanOutput + '\n```\n\n</details>')
      }
    }
  }

  return parts.join('\n\n')
}

export default function NotionEditor({ content, onChange, onImageUpload }) {
  const [slashMenu, setSlashMenu] = useState(null)
  const [showVideoEmbed, setShowVideoEmbed] = useState(false)
  const slashStartPos = useRef(null)
  const imageInputRef = useRef(null)
  const notebookInputRef = useRef(null)

  // 이미지 업로드 핸들러
  const handleImageUpload = useCallback(async (file) => {
    if (onImageUpload) {
      return await onImageUpload(file)
    }
    const formData = new FormData()
    formData.append('image', file)
    const { data } = await uploadImage(formData)
    return data.image
  }, [onImageUpload])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
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
      TaskItem.configure({ nested: true }),
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      Underline,
      Highlight.configure({ multicolor: true }),
      Typography,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Superscript,
      Subscript,
      CodeBlockLowlight.configure({ lowlight }),
      TextStyle,
      Color,
      Mathematics.configure({
        HTMLAttributes: { class: 'math-node' },
      }),
      CodeCell,
      MermaidBlock,
      CalloutBlock,
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
      handlePaste: (view, event) => {
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
      handleDrop: (view, event) => {
        const files = event.dataTransfer?.files
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
        return false
      },
    },
    onUpdate: ({ editor }) => {
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
      const textBefore = $from.parent.textContent.slice(0, $from.parentOffset)
      const slashMatch = textBefore.match(/(?:^|\s)\/([\w가-힣]*)$/)

      if (slashMatch) {
        const query = slashMatch[1] || ''
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

    const { state } = editor
    const from = slashStartPos.current
    const to = state.selection.$from.pos

    editor.chain().focus().deleteRange({ from, to }).run()

    if (item.id === 'image') {
      imageInputRef.current?.click()
    } else if (item.id === 'video') {
      setShowVideoEmbed(true)
    } else if (item.id === 'math') {
      editor.commands.insertBlockMath({ latex: 'E = mc^2' })
    } else if (item.id === 'notebook') {
      notebookInputRef.current?.click()
    } else if (item.id === 'mermaid') {
      editor.commands.setMermaidBlock('graph TD\n  A[Start] --> B[Process] --> C[End]')
    } else if (item.id === 'callout-info') {
      editor.commands.setCallout('info')
    } else if (item.id === 'callout-warning') {
      editor.commands.setCallout('warning')
    } else if (item.id === 'callout-tip') {
      editor.commands.setCallout('tip')
    } else if (item.id === 'bookmark') {
      const url = prompt('URL을 입력하세요:')
      if (url?.trim()) {
        editor.chain().focus().insertContent(`\n\n${url.trim()}\n\n`).run()
      }
    } else if (item.id === 'codecell') {
      editor.commands.setCodeCell({ language: 'python', code: '# code here' })
    } else if (item.command) {
      item.command(editor)
    }

    setSlashMenu(null)
    slashStartPos.current = null
  }, [editor])

  // 이미지 파일 선택
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
    if (imageInputRef.current) imageInputRef.current.value = ''
  }, [editor, handleImageUpload])

  // .ipynb 파일 선택
  const handleNotebookSelect = useCallback(async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const notebook = JSON.parse(text)
      const markdown = convertNotebookToContent(notebook)
      editor?.chain().focus().insertContent(markdown).run()
      toast.success(`Notebook imported: ${file.name}`)
    } catch (err) {
      toast.error('Failed to parse notebook: ' + err.message)
    }
    if (notebookInputRef.current) notebookInputRef.current.value = ''
  }, [editor])

  // 비디오 임베드
  const handleVideoEmbed = useCallback((videoInfo) => {
    if (!editor) return
    const iframeHtml = `<div class="video-embed"><iframe src="${videoInfo.embedUrl}" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;border-radius:8px;"></iframe></div><p></p>`
    editor.chain().focus().insertContent(iframeHtml).run()
    setShowVideoEmbed(false)
  }, [editor])

  if (!editor) return null

  return (
    <div className="notion-editor relative flex-1 flex flex-col overflow-hidden">
      <BubbleMenu
        editor={editor}
        tippyOptions={{ duration: 150, placement: 'top' }}
        className="bubble-menu"
      >
        <EditorToolbar editor={editor} />
      </BubbleMenu>

      <div className="flex-1 overflow-y-auto relative">
        <EditorContent editor={editor} className="notion-editor-wrapper" />

        {slashMenu && (
          <div
            className="absolute z-50"
            style={{ left: `${slashMenu.x}px`, top: `${slashMenu.y}px` }}
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

      {showVideoEmbed && (
        <div className="absolute bottom-4 left-4 right-4 z-40">
          <EmbedBlock
            onEmbed={handleVideoEmbed}
            onClose={() => setShowVideoEmbed(false)}
          />
        </div>
      )}

      <input ref={imageInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageFileSelect} />
      <input ref={notebookInputRef} type="file" accept=".ipynb" className="hidden" onChange={handleNotebookSelect} />
    </div>
  )
}
