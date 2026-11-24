import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { DocumentStatus } from '@/api/types'

interface DocumentStatusBadgeProps {
  status: DocumentStatus
  error?: string | null
}

export function DocumentStatusBadge({ status, error }: DocumentStatusBadgeProps) {
  if (status === 'processing' || status === 'uploaded') {
    return (
      <Badge
        variant='outline'
        className='border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-300 font-medium px-2.5 py-0.5 gap-1.5'
      >
        <Loader2 className='size-3.5 animate-spin text-amber-600 dark:text-amber-400' />
        <span>Processing</span>
      </Badge>
    )
  }

  if (status === 'ready') {
    return (
      <Badge
        variant='outline'
        className='border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 font-medium px-2.5 py-0.5 gap-1.5'
      >
        <CheckCircle2 className='size-3.5 text-emerald-600 dark:text-emerald-400' />
        <span>Ready</span>
      </Badge>
    )
  }

  if (status === 'failed') {
    const badge = (
      <Badge
        variant='outline'
        className='border-rose-500/30 bg-rose-500/10 text-rose-800 dark:text-rose-300 font-medium px-2.5 py-0.5 gap-1.5 cursor-help'
      >
        <AlertCircle className='size-3.5 text-rose-600 dark:text-rose-400' />
        <span>Failed</span>
      </Badge>
    )

    if (error) {
      return (
        <TooltipProvider>
          <Tooltip delayDuration={200}>
            <TooltipTrigger asChild>
              <span className='inline-flex cursor-help'>{badge}</span>
            </TooltipTrigger>
            <TooltipContent
              side='top'
              className='max-w-xs bg-popover text-popover-foreground border-border shadow-md p-2.5 text-xs'
            >
              <p className='font-semibold mb-1 text-destructive'>Ingestion Error:</p>
              <p className='break-words'>{error}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    }

    return badge
  }

  return (
    <Badge variant='outline' className='gap-1.5 text-muted-foreground'>
      <Clock className='size-3.5' />
      <span>{status}</span>
    </Badge>
  )
}

