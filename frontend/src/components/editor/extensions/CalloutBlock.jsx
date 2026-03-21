import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer, NodeViewWrapper, NodeViewContent } from '@tiptap/react'
import { Info, AlertTriangle, Lightbulb, AlertCircle } from 'lucide-react'

const CALLOUT_TYPES = {
  info: { icon: Info, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.08)', border: 'rgba(59, 130, 246, 0.3)', label: 'Info' },
  warning: { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.3)', label: 'Warning' },
  tip: { icon: Lightbulb, color: '#10b981', bg: 'rgba(16, 185, 129, 0.08)', border: 'rgba(16, 185, 129, 0.3)', label: 'Tip' },
  danger: { icon: AlertCircle, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)', border: 'rgba(239, 68, 68, 0.3)', label: 'Danger' },
}

const CalloutComponent = ({ node, updateAttributes }) => {
  const type = CALLOUT_TYPES[node.attrs.calloutType] || CALLOUT_TYPES.info
  const Icon = type.icon

  const cycleType = () => {
    const types = Object.keys(CALLOUT_TYPES)
    const idx = types.indexOf(node.attrs.calloutType)
    const next = types[(idx + 1) % types.length]
    updateAttributes({ calloutType: next })
  }

  return (
    <NodeViewWrapper
      className="callout-block my-3"
      style={{ background: type.bg, borderLeft: `4px solid ${type.border}`, borderRadius: '8px', padding: '1rem 1rem 1rem 0.75rem' }}
    >
      <div className="flex items-start gap-2">
        <button
          onClick={cycleType}
          contentEditable={false}
          className="shrink-0 mt-0.5 cursor-pointer hover:opacity-70"
          title="Click to change type"
        >
          <Icon size={18} style={{ color: type.color }} />
        </button>
        <div className="flex-1 min-w-0">
          <NodeViewContent className="callout-content" />
        </div>
      </div>
    </NodeViewWrapper>
  )
}

const CalloutBlock = Node.create({
  name: 'calloutBlock',
  group: 'block',
  content: 'block+',
  defining: true,

  addAttributes() {
    return {
      calloutType: { default: 'info' },
    }
  },

  parseHTML() {
    return [{
      tag: 'div[data-type="callout"]',
      getAttrs: (el) => ({ calloutType: el.getAttribute('data-callout-type') || 'info' }),
    }]
  },

  renderHTML({ node, HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, {
      'data-type': 'callout',
      'data-callout-type': node.attrs.calloutType,
    }), 0]
  },

  addNodeView() {
    return ReactNodeViewRenderer(CalloutComponent)
  },

  addCommands() {
    return {
      setCallout: (calloutType = 'info') => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: { calloutType },
          content: [{ type: 'paragraph', content: [{ type: 'text', text: '' }] }],
        })
      },
      toggleCallout: (calloutType = 'info') => ({ commands, state }) => {
        const { $from } = state.selection
        if ($from.parent.type.name === 'calloutBlock' || $from.node(-1)?.type.name === 'calloutBlock') {
          return commands.lift('calloutBlock')
        }
        return commands.setCallout(calloutType)
      },
    }
  },

  addStorage() {
    return {
      markdown: {
        serialize(state, node) {
          state.write(`:::${node.attrs.calloutType}\n`)
          state.renderContent(node)
          state.write(':::\n')
        },
        parse: {},
      },
    }
  },
})

export { CALLOUT_TYPES }
export default CalloutBlock
