import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer, NodeViewWrapper, NodeViewContent } from '@tiptap/react'
import { Info, AlertTriangle, Lightbulb, AlertCircle } from 'lucide-react'
import CARD_COLORS, { CALLOUT_MAP } from '../../../data/cardColors'

const CALLOUT_TYPES = {
  info:    { icon: Info,          ...CARD_COLORS[CALLOUT_MAP.info] },
  warning: { icon: AlertTriangle, ...CARD_COLORS[CALLOUT_MAP.warning] },
  tip:     { icon: Lightbulb,     ...CARD_COLORS[CALLOUT_MAP.tip] },
  danger:  { icon: AlertCircle,   ...CARD_COLORS[CALLOUT_MAP.danger] },
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
      style={{
        background: `rgba(${type.rgb}, 0.06)`,
        border: `1px solid rgba(${type.rgb}, 0.08)`,
        borderRadius: '12px',
        padding: '1rem 1.25rem',
      }}
    >
      <div className="flex flex-col gap-1">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, fontSize: '13px', color: type.hex, marginBottom: '2px' }}>
          <button
            onClick={cycleType}
            contentEditable={false}
            className="shrink-0 cursor-pointer hover:opacity-70 inline-flex"
            title="Click to change type"
          >
            <Icon size={16} style={{ color: type.hex }} />
          </button>
          <span>{type.label}</span>
        </div>
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
