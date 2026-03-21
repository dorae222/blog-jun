import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer, NodeViewWrapper } from '@tiptap/react'
import { useEffect, useRef, useState } from 'react'
import { AlertTriangle } from 'lucide-react'

const MermaidComponent = ({ node, updateAttributes }) => {
  const [svg, setSvg] = useState('')
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(!node.attrs.code)
  const textareaRef = useRef(null)
  const renderRef = useRef(0)

  useEffect(() => {
    const code = node.attrs.code
    if (!code) { setSvg(''); return }

    const currentRender = ++renderRef.current

    // 동적 import로 mermaid 로딩
    import('mermaid').then(({ default: mermaid }) => {
      mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })
      const id = `mermaid-${Date.now()}-${currentRender}`
      mermaid.render(id, code).then(({ svg: rendered }) => {
        if (currentRender === renderRef.current) {
          setSvg(rendered)
          setError(null)
        }
      }).catch(err => {
        if (currentRender === renderRef.current) {
          setError(err.message || 'Mermaid rendering failed')
          setSvg('')
        }
      })
    })
  }, [node.attrs.code])

  const handleCodeChange = (e) => {
    updateAttributes({ code: e.target.value })
  }

  return (
    <NodeViewWrapper className="mermaid-block my-4">
      {editing ? (
        <div className="mermaid-editor">
          <div className="mermaid-editor-header" contentEditable={false}>
            <span>Mermaid</span>
            <button onClick={() => setEditing(false)} className="mermaid-preview-btn">
              Preview
            </button>
          </div>
          <textarea
            ref={textareaRef}
            value={node.attrs.code || ''}
            onChange={handleCodeChange}
            className="mermaid-textarea"
            placeholder="graph TD\n  A[Start] --> B[End]"
            rows={6}
          />
        </div>
      ) : (
        <div
          className="mermaid-preview"
          contentEditable={false}
          onClick={() => setEditing(true)}
        >
          {error ? (
            <div className="mermaid-error">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          ) : svg ? (
            <div dangerouslySetInnerHTML={{ __html: svg }} />
          ) : (
            <div className="mermaid-placeholder">Click to edit Mermaid diagram</div>
          )}
        </div>
      )}
    </NodeViewWrapper>
  )
}

const MermaidBlock = Node.create({
  name: 'mermaidBlock',
  group: 'block',
  atom: true,

  addAttributes() {
    return {
      code: { default: '' },
    }
  },

  parseHTML() {
    return [{
      tag: 'div[data-type="mermaid-block"]',
      getAttrs: (el) => ({ code: el.getAttribute('data-code') || '' }),
    }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, {
      'data-type': 'mermaid-block',
      'data-code': HTMLAttributes.code,
    })]
  },

  addNodeView() {
    return ReactNodeViewRenderer(MermaidComponent)
  },

  addCommands() {
    return {
      setMermaidBlock: (code = '') => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: { code },
        })
      },
    }
  },

  addStorage() {
    return {
      markdown: {
        serialize(state, node) {
          state.write('```mermaid\n')
          state.write(node.attrs.code || '')
          state.write('\n```\n')
        },
        parse: {},
      },
    }
  },
})

export default MermaidBlock
