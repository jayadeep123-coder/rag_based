import { User, Sparkles, AlertCircle, RefreshCw, HelpCircle, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MarkdownRenderer } from './markdown-renderer'
import type { ChatMessage } from '../types'
import type { Citation } from '@/api/types'

interface ChatMessageItemProps {
  message: ChatMessage
  onSelectCitation: (citation: Citation) => void
  onSuggestionClick?: (text: string) => void
  onRetry?: () => void
}

export function ChatMessageItem({
  message,
  onSelectCitation,
  onSuggestionClick,
  onRetry,
}: ChatMessageItemProps) {
  const isUser = message.role === 'user'

  // User Message
  if (isUser) {
    return (
      <div className='flex justify-end gap-2.5 my-3'>
        <div className='flex max-w-[85%] sm:max-w-[75%] flex-col items-end'>
          <div className='rounded-2xl rounded-tr-xs bg-primary px-4 py-2.5 text-primary-foreground shadow-xs'>
            <p className='text-sm leading-relaxed whitespace-pre-wrap font-sans'>
              {message.content}
            </p>
          </div>
          <span className='mt-1 text-[11px] text-muted-foreground'>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className='flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary'>
          <User className='size-4' />
        </div>
      </div>
    )
  }

  // Error State Message
  if (message.isError) {
    return (
      <div className='flex justify-start gap-2.5 my-3'>
        <div className='flex size-8 shrink-0 items-center justify-center rounded-full bg-destructive/15 text-destructive'>
          <AlertCircle className='size-4' />
        </div>
        <div className='flex max-w-[85%] sm:max-w-[75%] flex-col'>
          <div className='rounded-2xl rounded-tl-xs border border-destructive/30 bg-destructive/10 p-4 text-destructive shadow-xs space-y-2'>
            <p className='text-sm leading-relaxed'>{message.content}</p>
            {onRetry && (
              <Button
                variant='outline'
                size='sm'
                onClick={onRetry}
                className='h-7 gap-1.5 border-destructive/30 bg-card text-destructive hover:bg-destructive/10 text-xs'
              >
                <RefreshCw className='size-3' />
                <span>Retry Question</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Assistant Not Found Fallback (found === false)
  if (message.found === false) {
    return (
      <div className='flex justify-start gap-2.5 my-3'>
        <div className='flex size-8 shrink-0 items-center justify-center rounded-full bg-accent/40 text-accent-foreground'>
          <HelpCircle className='size-4' />
        </div>
        <div className='flex max-w-[85%] sm:max-w-[80%] flex-col'>
          <div className='rounded-2xl rounded-tl-xs border border-border/80 bg-muted/40 p-4 shadow-xs space-y-3'>
            <div className='flex items-start gap-2.5'>
              <div className='text-sm text-foreground leading-relaxed'>
                <p className='font-medium text-foreground mb-1'>Not Found in Document</p>
                <p className='text-muted-foreground'>{message.content}</p>
              </div>
            </div>

            {/* Suggestions */}
            {onSuggestionClick && (
              <div className='pt-2 border-t border-border/60'>
                <p className='text-xs font-semibold text-muted-foreground mb-2'>Try asking:</p>
                <div className='flex flex-wrap gap-1.5'>
                  <Button
                    variant='outline'
                    size='sm'
                    className='h-7 text-xs bg-card hover:bg-accent/20 hover:text-accent-foreground'
                    onClick={() => onSuggestionClick('Rephrase your question with different keywords')}
                  >
                    Rephrase with different terms
                  </Button>
                  <Button
                    variant='outline'
                    size='sm'
                    className='h-7 text-xs bg-card hover:bg-accent/20 hover:text-accent-foreground'
                    onClick={() => onSuggestionClick('Summarize the main topics in this document')}
                  >
                    Summarize main topics
                  </Button>
                  <Button
                    variant='outline'
                    size='sm'
                    className='h-7 text-xs bg-card hover:bg-accent/20 hover:text-accent-foreground'
                    onClick={() => onSuggestionClick('What are the key definitions or concepts?')}
                  >
                    Key definitions & concepts
                  </Button>
                </div>
              </div>
            )}
          </div>
          <span className='mt-1 text-[11px] text-muted-foreground'>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    )
  }

  // Unique cited pages for the Sources row
  const citations = message.citations || []
  const uniqueCitations = Array.from(
    new Map(citations.map((c) => [c.ref, c])).values()
  )

  // Standard Grounded Assistant Message
  return (
    <div className='flex justify-start gap-2.5 my-3'>
      <div className='flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-2xs'>
        <Sparkles className='size-4' />
      </div>

      <div className='flex max-w-[85%] sm:max-w-[80%] flex-col'>
        <div className='rounded-2xl rounded-tl-xs border border-border/80 bg-card p-4 shadow-xs text-foreground'>
          <MarkdownRenderer
            content={message.content}
            citations={message.citations}
            onSelectCitation={onSelectCitation}
          />

          {/* Sources Summary Row */}
          {uniqueCitations.length > 0 && (
            <div className='mt-4 pt-3 border-t border-border/60 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground'>
              <span className='flex items-center gap-1 font-semibold text-foreground/80 mr-1'>
                <BookOpen className='size-3.5 text-primary' />
                Sources:
              </span>
              {uniqueCitations.map((c) => {
                const pageLabel =
                  c.page_start === c.page_end
                    ? `Page ${c.page_start}`
                    : `Pages ${c.page_start}–${c.page_end}`
                return (
                  <button
                    key={`source-row-${c.ref}`}
                    type='button'
                    onClick={() => onSelectCitation(c)}
                    className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-accent/60 bg-accent/20 text-accent-foreground text-xs font-medium hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer'
                  >
                    <span className='font-bold'>[{c.ref}]</span>
                    <span>{pageLabel}</span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <span className='mt-1 text-[11px] text-muted-foreground'>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}
