import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer, NodeViewWrapper, NodeViewContent } from '@tiptap/react'
import { useState } from 'react'
import { ChevronDown, ChevronRight, Terminal } from 'lucide-react'

// 코드 + 실행 결과 블록 (Jupyter 스타일)
const CodeCellComponent = ({ node, updateAttributes }) => {
  const [collapsed, setCollapsed] = useState(node.attrs.collapsed)

  const toggleCollapsed = () => {
    const next = !collapsed
    setCollapsed(next)
    updateAttributes({ collapsed: next })
  }

  return (
    <NodeViewWrapper className="code-cell my-4">
      {/* 코드 영역 */}
      <div className="code-cell-code">
        <div className="code-cell-header">
          <span className="code-cell-lang">{node.attrs.language || 'python'}</span>
        </div>
        <NodeViewContent as="pre" className="code-cell-pre" />
      </div>

      {/* 결과 영역 */}
      {node.attrs.output && (
        <div className="code-cell-output">
          <button
            className="code-cell-output-toggle"
            onClick={toggleCollapsed}
            contentEditable={false}
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
            <Terminal size={14} />
            <span>Output</span>
          </button>
          {!collapsed && (
            <pre className="code-cell-output-content" contentEditable={false}>
              {node.attrs.output}
            </pre>
          )}
        </div>
      )}
    </NodeViewWrapper>
  )
}

const CodeCell = Node.create({
  name: 'codeCell',
  group: 'block',
  content: 'text*',
  marks: '',
  code: true,
  defining: true,

  addAttributes() {
    return {
      language: { default: 'python' },
      output: { default: '' },
      collapsed: { default: false },
    }
  },

  parseHTML() {
    return [{
      tag: 'div[data-type="code-cell"]',
      getAttrs: (el) => ({
        language: el.getAttribute('data-language') || 'python',
        output: el.getAttribute('data-output') || '',
        collapsed: el.getAttribute('data-collapsed') === 'true',
      }),
    }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, {
      'data-type': 'code-cell',
      'data-language': HTMLAttributes.language,
      'data-output': HTMLAttributes.output,
      'data-collapsed': HTMLAttributes.collapsed,
    }), ['pre', ['code', 0]]]
  },

  addNodeView() {
    return ReactNodeViewRenderer(CodeCellComponent)
  },

  addCommands() {
    return {
      setCodeCell: (attrs = {}) => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: { language: 'python', ...attrs },
          content: [{ type: 'text', text: attrs.code || '# code here' }],
        })
      },
    }
  },

  // 마크다운 직렬화: ```lang\ncode\n``` + :::output\nresult\n:::
  addStorage() {
    return {
      markdown: {
        serialize(state, node) {
          state.write(`\`\`\`${node.attrs.language || ''}\n`)
          state.text(node.textContent, false)
          state.write('\n```\n')
          if (node.attrs.output) {
            state.write(`\n<details><summary>Output</summary>\n\n\`\`\`\n${node.attrs.output}\n\`\`\`\n\n</details>\n`)
          }
        },
        parse: {
          // 파싱은 기본 코드블록으로 fallback
        },
      },
    }
  },
})

export default CodeCell
