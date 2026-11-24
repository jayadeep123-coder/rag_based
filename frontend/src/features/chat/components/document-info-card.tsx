import { Link } from '@tanstack/react-router'
import { ArrowLeft, FileText, BookOpen, Layers, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DocumentStatusBadge } from '@/features/documents/components/document-status-badge'
import type { DocumentDetail } from '@/api/types'

interface DocumentInfoCardProps {
  document: DocumentDetail | null
}

export function DocumentInfoCard({ document }: DocumentInfoCardProps) {
  if (!document) return null

  return (
    <Card className='border-border/80 bg-card shadow-xs'>
      <CardHeader className='p-4 pb-3'>
        <div className='flex items-center justify-between mb-2'>
          <Button variant='ghost' size='sm' asChild className='-ml-2 h-7 px-2 text-xs text-muted-foreground hover:text-foreground'>
            <Link to='/documents' className='gap-1.5'>
              <ArrowLeft className='size-3.5' />
              <span>Documents</span>
            </Link>
          </Button>
          <DocumentStatusBadge status={document.status} error={document.error} />
        </div>

        <div className='flex items-start gap-2.5'>
          <div className='flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary mt-0.5'>
            <FileText className='size-4' />
          </div>
          <div className='min-w-0'>
            <CardTitle className='text-sm font-semibold text-foreground truncate' title={document.filename}>
              {document.filename}
            </CardTitle>
            <p className='text-xs text-muted-foreground font-mono truncate'>
              {document.id.slice(0, 8)}...
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className='p-4 pt-0 space-y-2.5 text-xs text-muted-foreground border-t border-border/50 mt-3 pt-3'>
        <div className='flex items-center justify-between'>
          <span className='flex items-center gap-1.5'>
            <BookOpen className='size-3.5 text-primary' />
            Page Count:
          </span>
          <span className='font-semibold text-foreground'>
            {document.page_count ?? '—'} {document.page_count === 1 ? 'page' : 'pages'}
          </span>
        </div>

        <div className='flex items-center justify-between'>
          <span className='flex items-center gap-1.5'>
            <Layers className='size-3.5 text-primary' />
            Indexed Chunks:
          </span>
          <span className='font-semibold text-foreground'>
            {document.chunk_count ?? '—'}
          </span>
        </div>

        <div className='flex items-center justify-between'>
          <span className='flex items-center gap-1.5'>
            <ShieldCheck className='size-3.5 text-emerald-600' />
            Source Grounding:
          </span>
          <span className='font-medium text-foreground'>
            Answers use this PDF only
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

