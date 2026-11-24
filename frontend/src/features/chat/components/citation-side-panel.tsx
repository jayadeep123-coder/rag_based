import { useState, useEffect } from 'react'
import { X, ChevronLeft, ChevronRight, BookOpen, Sparkles, FileText, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Citation } from '@/api/types'

interface CitationSidePanelProps {
  citation: Citation | null
  citations: Citation[]
  onClose: () => void
  onNavigate: (citation: Citation) => void
}

export function CitationSidePanel({
  citation,
  citations,
  onClose,
  onNavigate,
}: CitationSidePanelProps) {
  const [showFullText, setShowFullText] = useState(false)

  // Reset full text toggle when switching to a different citation
  useEffect(() => {
    setShowFullText(false)
  }, [citation?.ref, citation?.chunk_id])

  // Listen for Escape key to close the side panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!citation) return null

  const currentIndex = citations.findIndex((c) => c.ref === citation.ref)
  const hasPrev = currentIndex > 0
  const hasNext = currentIndex >= 0 && currentIndex < citations.length - 1

  const handlePrev = () => {
    if (hasPrev) {
      onNavigate(citations[currentIndex - 1])
    }
  }

  const handleNext = () => {
    if (hasNext) {
      onNavigate(citations[currentIndex + 1])
    }
  }

  const pageRangeText =
    citation.page_start === citation.page_end
      ? `Page ${citation.page_start}`
      : `Pages ${citation.page_start}–${citation.page_end}`

  const similarityPercentage = Math.round(citation.similarity * 100)
  const hasFullText = Boolean(citation.full_text && citation.full_text.trim() !== citation.snippet.trim())

  return (
    <aside
      aria-label='Citation Source Details'
      className='flex h-full w-full flex-col border-l border-border/80 bg-card shadow-lg md:w-96 shrink-0 transition-all duration-200 min-h-0'
    >
      {/* Panel Header */}
      <div className='flex items-center justify-between border-b border-border/80 p-4 bg-muted/20 shrink-0'>
        <div className='flex items-center gap-2'>
          <span className='flex size-7 items-center justify-center rounded-md bg-accent text-accent-foreground font-bold text-xs'>
            [{citation.ref}]
          </span>
          <div>
            <h3 className='text-sm font-semibold text-foreground leading-none'>Source Details</h3>
            <p className='text-xs text-muted-foreground mt-0.5'>{pageRangeText}</p>
          </div>
        </div>

        <div className='flex items-center gap-1'>
          <Button
            variant='ghost'
            size='icon'
            onClick={onClose}
            className='size-8 text-muted-foreground hover:text-foreground'
            aria-label='Close citation panel'
          >
            <X className='size-4' />
          </Button>
        </div>
      </div>

      {/* Metadata Badges */}
      <div className='flex items-center gap-2 px-4 py-2.5 border-b border-border/60 bg-card text-xs shrink-0'>
        <Badge variant='outline' className='gap-1 border-primary/20 bg-primary/5 text-primary text-xs font-medium'>
          <BookOpen className='size-3' />
          <span>{pageRangeText}</span>
        </Badge>

        <Badge
          variant='outline'
          title='Similarity between your question and this passage (not an accuracy score)'
          className='gap-1 border-accent text-accent-foreground bg-accent/30 text-xs font-semibold cursor-help'
        >
          <Sparkles className='size-3 text-primary' />
          <span>{similarityPercentage}% Relevance</span>
        </Badge>
      </div>

      {/* Snippet Content Area */}
      <div className='flex-1 min-h-0 overflow-y-auto p-4 space-y-3.5'>
        <div className='space-y-2'>
          <div className='flex items-center justify-between'>
            <span className='text-xs font-semibold tracking-wider uppercase text-muted-foreground flex items-center gap-1.5'>
              <FileText className='size-3.5 text-primary' />
              {showFullText ? 'Full Extracted Passage' : 'Key Supporting Sentences'}
            </span>

            {hasFullText && (
              <Button
                variant='ghost'
                size='sm'
                onClick={() => setShowFullText(!showFullText)}
                className='h-6 px-2 text-[11px] text-primary hover:text-primary hover:bg-primary/10'
              >
                {showFullText ? 'Show key sentences only' : 'Show full passage'}
              </Button>
            )}
          </div>

          {showFullText && citation.full_text ? (
            <div className='rounded-xl border border-border/70 bg-muted/30 p-3.5 text-sm leading-relaxed text-foreground font-sans'>
              {citation.char_start !== undefined &&
              citation.char_end !== undefined &&
              citation.char_start >= 0 &&
              citation.char_end <= citation.full_text.length &&
              citation.char_start < citation.char_end ? (
                <p className='break-words leading-relaxed'>
                  {citation.full_text.slice(0, citation.char_start)}
                  <mark className='rounded bg-accent/40 px-1 py-0.5 font-medium text-accent-foreground'>
                    {citation.full_text.slice(citation.char_start, citation.char_end)}
                  </mark>
                  {citation.full_text.slice(citation.char_end)}
                </p>
              ) : (
                <div className='space-y-2.5 break-words leading-relaxed'>
                  {citation.full_text.split(/\n\n+/).map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className='rounded-xl border border-accent/40 bg-accent/15 p-3.5 text-sm leading-relaxed text-foreground font-sans'>
              <p className='break-words leading-relaxed'>
                {citation.context_before && (
                  <span className='text-muted-foreground/80 font-normal'>
                    {citation.context_before}{' '}
                  </span>
                )}
                <mark className='rounded bg-accent/45 px-1 py-0.5 font-medium text-accent-foreground'>
                  {citation.snippet}
                </mark>
                {citation.context_after && (
                  <span className='text-muted-foreground/80 font-normal'>
                    {' '}{citation.context_after}
                  </span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* Source passage used card without unverified verification claims */}
        <div className='rounded-lg border border-border/70 bg-muted/40 p-3 text-xs text-muted-foreground flex items-start gap-2'>
          <Check className='size-3.5 text-primary shrink-0 mt-0.5' />
          <p className='leading-normal'>
            Source passage used for this answer
          </p>
        </div>
      </div>

      {/* Navigation Footer */}
      {citations.length > 1 && (
        <div className='flex items-center justify-between border-t border-border/80 p-3 bg-muted/10 shrink-0'>
          <Button
            variant='outline'
            size='sm'
            onClick={handlePrev}
            disabled={!hasPrev}
            className='h-8 gap-1 text-xs'
          >
            <ChevronLeft className='size-3.5' />
            <span>Previous</span>
          </Button>

          <span className='text-xs text-muted-foreground font-mono'>
            {currentIndex + 1} of {citations.length}
          </span>

          <Button
            variant='outline'
            size='sm'
            onClick={handleNext}
            disabled={!hasNext}
            className='h-8 gap-1 text-xs'
          >
            <span>Next</span>
            <ChevronRight className='size-3.5' />
          </Button>
        </div>
      )}
    </aside>
  )
}
