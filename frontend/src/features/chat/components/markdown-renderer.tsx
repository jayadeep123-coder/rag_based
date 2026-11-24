import React from 'react'
import { CitationChip } from './citation-chip'
import type { Citation } from '@/api/types'

interface MarkdownRendererProps {
  content: string
  citations?: Citation[]
  onSelectCitation: (citation: Citation) => void
}

export function MarkdownRenderer({
  content,
  citations = [],
  onSelectCitation,
}: MarkdownRendererProps) {
  // Build a lookup map of citations by ref number
  const citationMap = React.useMemo(() => {
    const map = new Map<number, Citation>()
    citations.forEach((c) => map.set(c.ref, c))
    return map
  }, [citations])

  // Helper to parse inline formatting (bold, italic, code, citations) into React elements
  const parseInline = (text: string): React.ReactNode[] => {
    // Splits text by citation chips, inline code, bold-italic, bold, and italic
    const tokenRegex = /(\[\d+\]|`[^`]+`|\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*)/g
    const tokens = text.split(tokenRegex)

    return tokens.map((token, idx) => {
      if (!token) return null

      // 1. Citation tag: [1]
      const citMatch = token.match(/^\[(\d+)\]$/)
      if (citMatch) {
        const refNum = parseInt(citMatch[1], 10)
        const cit = citationMap.get(refNum)
        if (cit) {
          return (
            <CitationChip
              key={`cit-${idx}-${refNum}`}
              refNumber={refNum}
              citation={cit}
              onClick={onSelectCitation}
            />
          )
        }
        return <span key={`text-cit-${idx}`}>[{refNum}]</span>
      }

      // 2. Inline code: `code`
      if (token.startsWith('`') && token.endsWith('`') && token.length > 2) {
        return (
          <code
            key={`code-${idx}`}
            className='rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground font-medium'
          >
            {token.slice(1, -1)}
          </code>
        )
      }

      // 3. Bold + Italic: ***text***
      if (token.startsWith('***') && token.endsWith('***') && token.length > 6) {
        return (
          <strong key={`bi-${idx}`} className='font-bold italic text-foreground'>
            {token.slice(3, -3)}
          </strong>
        )
      }

      // 4. Bold: **text**
      if (token.startsWith('**') && token.endsWith('**') && token.length > 4) {
        return (
          <strong key={`bold-${idx}`} className='font-bold text-foreground'>
            {token.slice(2, -2)}
          </strong>
        )
      }

      // 5. Italic: *text*
      if (token.startsWith('*') && token.endsWith('*') && token.length > 2) {
        return (
          <em key={`italic-${idx}`} className='italic text-foreground'>
            {token.slice(1, -1)}
          </em>
        )
      }

      // 6. Plain text: strip any accidental remaining raw '*' characters
      const cleanPlain = token.replace(/\*/g, '')
      return <span key={`plain-${idx}`}>{cleanPlain}</span>
    })
  }

  // Parse lines into blocks (headers, code blocks, bullet lists, numbered lists, blockquotes, paragraphs)
  const blocks: React.ReactNode[] = []
  const lines = content.split('\n')
  let inCodeBlock = false
  let codeBlockLines: string[] = []
  let listItems: React.ReactNode[] = []
  let isOrderedList = false

  const flushList = () => {
    if (listItems.length > 0) {
      if (isOrderedList) {
        blocks.push(
          <ol
            key={`ol-${blocks.length}`}
            className='my-2 ml-5 list-decimal space-y-1.5 text-sm leading-relaxed text-foreground'
          >
            {listItems}
          </ol>
        )
      } else {
        blocks.push(
          <ul
            key={`ul-${blocks.length}`}
            className='my-2 ml-5 list-disc space-y-1.5 text-sm leading-relaxed text-foreground'
          >
            {listItems}
          </ul>
        )
      }
      listItems = []
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]
    const trimmed = rawLine.trim()

    // 1. Code blocks: ```
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        blocks.push(
          <pre
            key={`codeblock-${blocks.length}`}
            className='my-2 overflow-x-auto rounded-lg border border-border/80 bg-muted/60 p-3 font-mono text-xs text-foreground leading-relaxed'
          >
            <code>{codeBlockLines.join('\n')}</code>
          </pre>
        )
        codeBlockLines = []
        inCodeBlock = false
      } else {
        flushList()
        inCodeBlock = true
      }
      continue
    }

    if (inCodeBlock) {
      codeBlockLines.push(rawLine)
      continue
    }

    // 2. Empty line breaks paragraphs & lists
    if (!trimmed) {
      flushList()
      continue
    }

    // 3. Horizontal rule: --- or ***
    if (/^(\s*[-*_]\s*){3,}$/.test(rawLine)) {
      flushList()
      blocks.push(<hr key={`hr-${blocks.length}`} className='my-3 border-border/80' />)
      continue
    }

    // 4. Headers: #, ##, ###, ####
    if (trimmed.startsWith('#### ')) {
      flushList()
      blocks.push(
        <h5 key={`h5-${blocks.length}`} className='mt-3 mb-1 text-xs font-bold uppercase tracking-wider text-muted-foreground'>
          {parseInline(trimmed.slice(5))}
        </h5>
      )
      continue
    }
    if (trimmed.startsWith('### ')) {
      flushList()
      blocks.push(
        <h4 key={`h4-${blocks.length}`} className='mt-3 mb-1 text-sm font-bold text-foreground'>
          {parseInline(trimmed.slice(4))}
        </h4>
      )
      continue
    }
    if (trimmed.startsWith('## ')) {
      flushList()
      blocks.push(
        <h3 key={`h3-${blocks.length}`} className='mt-4 mb-1.5 text-base font-bold text-foreground'>
          {parseInline(trimmed.slice(3))}
        </h3>
      )
      continue
    }
    if (trimmed.startsWith('# ')) {
      flushList()
      blocks.push(
        <h2 key={`h2-${blocks.length}`} className='mt-4 mb-2 text-lg font-bold text-foreground'>
          {parseInline(trimmed.slice(2))}
        </h2>
      )
      continue
    }

    // 5. Blockquote: >
    if (trimmed.startsWith('> ')) {
      flushList()
      blocks.push(
        <blockquote
          key={`quote-${blocks.length}`}
          className='my-2 border-l-2 border-primary/50 pl-3 italic text-muted-foreground text-sm'
        >
          {parseInline(trimmed.slice(2))}
        </blockquote>
      )
      continue
    }

    // 6. List items: matches optional indent + bullet ('-' or '*') or numbered list ('1.')
    const listMatch = rawLine.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/)
    if (listMatch) {
      const indent = listMatch[1].length
      const marker = listMatch[2]
      const itemText = listMatch[3]
      const isNum = /^\d+\./.test(marker)

      if (listItems.length > 0 && isNum !== isOrderedList) {
        flushList()
      }
      isOrderedList = isNum

      const isNested = indent >= 2
      listItems.push(
        <li
          key={`li-${listItems.length}`}
          className={isNested ? 'ml-5 list-[circle] mt-1' : 'mt-1'}
        >
          {parseInline(itemText)}
        </li>
      )
      continue
    }

    // 7. Regular paragraph
    flushList()
    blocks.push(
      <p key={`p-${blocks.length}`} className='my-1.5 text-sm leading-relaxed text-foreground'>
        {parseInline(trimmed)}
      </p>
    )
  }

  flushList()

  return <div className='space-y-1'>{blocks}</div>
}
