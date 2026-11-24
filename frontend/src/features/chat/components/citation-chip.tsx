import type { Citation } from '@/api/types'

interface CitationChipProps {
  refNumber: number
  citation?: Citation
  onClick: (citation: Citation) => void
}

export function CitationChip({ refNumber, citation, onClick }: CitationChipProps) {
  if (!citation) {
    // If ref does not exist in response citations, render as plain bracketed text
    return <span className='text-muted-foreground'>[{refNumber}]</span>
  }

  const pageLabel =
    citation.page_start === citation.page_end
      ? `page ${citation.page_start}`
      : `pages ${citation.page_start}-${citation.page_end}`

  return (
    <button
      type='button'
      onClick={() => onClick(citation)}
      aria-label={`Source ${refNumber}, ${pageLabel}`}
      className='inline-flex items-center justify-center align-baseline px-1.5 py-0.2 mx-0.5 rounded text-xs font-bold bg-accent text-accent-foreground hover:bg-accent/80 hover:ring-1 hover:ring-accent-foreground/30 transition-all cursor-pointer shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring'
      title={`Source [${refNumber}]: Click to view snippet on ${pageLabel}`}
    >
      [{refNumber}]
    </button>
  )
}

