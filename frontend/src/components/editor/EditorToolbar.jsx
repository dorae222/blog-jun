import {
  Bold, Italic, Underline as UnderlineIcon, Strikethrough,
  Code, Link, Highlighter, ChevronDown
} from 'lucide-react'
import { useState, useCallback } from 'react'

const BLOCK_TYPES = [
  { label: 'Text', action: (editor) => editor.chain().focus().setParagraph().run(), check: (editor) => editor.isActive('paragraph') },
  { label: 'Heading 1', action: (editor) => editor.chain().focus().toggleHeading({ level: 1 }).run(), check: (editor) => editor.isActive('heading', { level: 1 }) },
  { label: 'Heading 2', action: (editor) => editor.chain().focus().toggleHeading({ level: 2 }).run(), check: (editor) => editor.isActive('heading', { level: 2 }) },
  { label: 'Heading 3', action: (editor) => editor.chain().focus().toggleHeading({ level: 3 }).run(), check: (editor) => editor.isActive('heading', { level: 3 }) },
  { label: 'Quote', action: (editor) => editor.chain().focus().toggleBlockquote().run(), check: (editor) => editor.isActive('blockquote') },
  { label: 'Code Block', action: (editor) => editor.chain().focus().toggleCodeBlock().run(), check: (editor) => editor.isActive('codeBlock') },
]

function ToolbarButton({ icon: Icon, isActive, onClick, title }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="p-1.5 rounded transition-colors"
      style={{
        background: isActive ? 'var(--bg-secondary)' : 'transparent',
        color: isActive ? 'var(--text)' : 'var(--text-secondary)',
      }}
    >
      <Icon size={15} />
    </button>
  )
}

export default function EditorToolbar({ editor }) {
  const [showBlockMenu, setShowBlockMenu] = useState(false)

  const setLink = useCallback(() => {
    if (editor.isActive('link')) {
      editor.chain().focus().unsetLink().run()
      return
    }
    const url = window.prompt('URL:')
    if (url) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    }
  }, [editor])

  if (!editor) return null

  const currentBlock = BLOCK_TYPES.find(b => b.check(editor)) || BLOCK_TYPES[0]

  return (
    <div
      className="flex items-center gap-0.5 px-2 py-1 rounded-lg shadow-lg border"
      style={{
        background: 'var(--bg)',
        borderColor: 'var(--border)',
      }}
    >
      {/* Block type dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowBlockMenu(!showBlockMenu)}
          className="flex items-center gap-1 px-2 py-1 rounded text-sm transition-colors hover:bg-gray-100"
          style={{ color: 'var(--text)' }}
        >
          {currentBlock.label}
          <ChevronDown size={14} />
        </button>
        {showBlockMenu && (
          <div
            className="absolute top-full left-0 mt-1 rounded-lg shadow-lg border overflow-hidden z-50"
            style={{ background: 'var(--bg)', borderColor: 'var(--border)', minWidth: '140px' }}
          >
            {BLOCK_TYPES.map(block => (
              <button
                key={block.label}
                onClick={() => { block.action(editor); setShowBlockMenu(false) }}
                className="w-full text-left px-3 py-1.5 text-sm transition-colors"
                style={{
                  background: block.check(editor) ? 'var(--bg-secondary)' : 'transparent',
                  color: 'var(--text)',
                }}
              >
                {block.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="w-px h-5 mx-1" style={{ background: 'var(--border)' }} />

      {/* Inline format buttons */}
      <ToolbarButton icon={Bold} isActive={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()} title="Bold" />
      <ToolbarButton icon={Italic} isActive={editor.isActive('italic')} onClick={() => editor.chain().focus().toggleItalic().run()} title="Italic" />
      <ToolbarButton icon={UnderlineIcon} isActive={editor.isActive('underline')} onClick={() => editor.chain().focus().toggleUnderline().run()} title="Underline" />
      <ToolbarButton icon={Strikethrough} isActive={editor.isActive('strike')} onClick={() => editor.chain().focus().toggleStrike().run()} title="Strikethrough" />
      <ToolbarButton icon={Code} isActive={editor.isActive('code')} onClick={() => editor.chain().focus().toggleCode().run()} title="Inline Code" />
      <ToolbarButton icon={Link} isActive={editor.isActive('link')} onClick={setLink} title="Link" />
      <ToolbarButton icon={Highlighter} isActive={editor.isActive('highlight')} onClick={() => editor.chain().focus().toggleHighlight().run()} title="Highlight" />
    </div>
  )
}
