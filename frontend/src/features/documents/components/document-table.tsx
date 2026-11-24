import { Link } from '@tanstack/react-router'
import { FileText, MessageSquare, Trash2, Calendar, BookOpen, RotateCw } from 'lucide-react'
import { format } from 'date-fns'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { DocumentStatusBadge } from './document-status-badge'
import type { DocumentItem } from '@/api/types'

interface DocumentTableProps {
  documents: DocumentItem[]
  onDelete: (doc: DocumentItem) => void
  onRetry?: (doc: DocumentItem) => void
}

export function DocumentTable({ documents, onDelete, onRetry }: DocumentTableProps) {
  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy')
    } catch {
      return dateStr
    }
  }

  return (
    <>
      {/* Desktop Table View */}
      <div className='hidden md:block rounded-xl border border-border/80 bg-card overflow-hidden shadow-xs'>
        <Table>
          <TableHeader className='bg-muted/40'>
            <TableRow className='hover:bg-transparent border-border/80'>
              <TableHead className='font-semibold text-foreground w-[40%]'>Document</TableHead>
              <TableHead className='font-semibold text-foreground'>Uploaded</TableHead>
              <TableHead className='font-semibold text-foreground text-center'>Pages</TableHead>
              <TableHead className='font-semibold text-foreground'>Status</TableHead>
              <TableHead className='font-semibold text-foreground text-right'>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => {
              const isReady = doc.status === 'ready'
              return (
                <TableRow
                  key={doc.id}
                  className='border-border/60 hover:bg-muted/20 transition-colors'
                >
                  <TableCell className='font-medium'>
                    <div className='flex items-center gap-3'>
                      <div className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary'>
                        <FileText className='size-4' />
                      </div>
                      <div className='min-w-0'>
                        <p className='truncate max-w-[280px] lg:max-w-[360px] font-medium text-foreground' title={doc.filename}>
                          {doc.filename}
                        </p>
                        <p className='text-xs text-muted-foreground font-mono truncate max-w-[200px]'>
                          ID: {doc.id.slice(0, 8)}...
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className='text-muted-foreground text-sm whitespace-nowrap'>
                    {formatDate(doc.created_at)}
                  </TableCell>
                  <TableCell className='text-center text-sm font-medium'>
                    {doc.page_count !== null && doc.page_count !== undefined ? (
                      <span className='inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground'>
                        <BookOpen className='size-3' />
                        {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}
                      </span>
                    ) : (
                      <span className='text-muted-foreground'>—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <DocumentStatusBadge status={doc.status} error={doc.error} />
                  </TableCell>
                  <TableCell className='text-right'>
                    <div className='flex items-center justify-end gap-2'>
                      {isReady ? (
                        <Button
                          variant='outline'
                          size='sm'
                          asChild
                          className='h-8 gap-1.5 border-primary/30 text-primary hover:bg-primary/10 hover:text-primary'
                        >
                          <Link to='/chat/$documentId' params={{ documentId: doc.id }}>
                            <MessageSquare className='size-3.5' />
                            <span>Chat</span>
                          </Link>
                        </Button>
                      ) : (
                        <TooltipProvider>
                          <Tooltip delayDuration={200}>
                            <TooltipTrigger asChild>
                              <span tabIndex={0}>
                                <Button
                                  variant='outline'
                                  size='sm'
                                  disabled
                                  className='h-8 gap-1.5 opacity-50 cursor-not-allowed'
                                >
                                  <MessageSquare className='size-3.5' />
                                  <span>Chat</span>
                                </Button>
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side='left' className='text-xs'>
                              {doc.status === 'processing'
                                ? 'Chat unlocks once ingestion completes.'
                                : 'Ingestion failed. Delete and re-upload standard PDF.'}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}

                      {doc.status === 'failed' && onRetry && (
                        <Button
                          variant='outline'
                          size='sm'
                          onClick={() => onRetry(doc)}
                          className='h-8 gap-1.5 border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10'
                          title='Retry processing this document'
                        >
                          <RotateCw className='size-3.5' />
                          <span>Retry</span>
                        </Button>
                      )}

                      <Button
                        variant='ghost'
                        size='icon'
                        onClick={() => onDelete(doc)}
                        className='size-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10'
                        title='Delete document'
                        aria-label={`Delete ${doc.filename}`}
                      >
                        <Trash2 className='size-4' />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Mobile Card View */}
      <div className='md:hidden space-y-3'>
        {documents.map((doc) => {
          const isReady = doc.status === 'ready'
          return (
            <Card key={doc.id} className='border-border/80 bg-card shadow-xs'>
              <CardContent className='p-4 space-y-3'>
                <div className='flex items-start justify-between gap-2'>
                  <div className='flex items-start gap-2.5 min-w-0'>
                    <div className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary mt-0.5'>
                      <FileText className='size-4' />
                    </div>
                    <div className='min-w-0'>
                      <p className='font-semibold text-foreground text-sm truncate' title={doc.filename}>
                        {doc.filename}
                      </p>
                      <div className='flex items-center gap-2 text-xs text-muted-foreground mt-0.5'>
                        <span className='flex items-center gap-1'>
                          <Calendar className='size-3' />
                          {formatDate(doc.created_at)}
                        </span>
                        {doc.page_count && (
                          <span>• {doc.page_count} pages</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <DocumentStatusBadge status={doc.status} error={doc.error} />
                </div>

                <div className='flex items-center justify-end gap-2 pt-1 border-t border-border/50'>
                  {isReady ? (
                    <Button
                      variant='outline'
                      size='sm'
                      asChild
                      className='h-8 gap-1.5 border-primary/30 text-primary hover:bg-primary/10 w-full justify-center'
                    >
                      <Link to='/chat/$documentId' params={{ documentId: doc.id }}>
                        <MessageSquare className='size-3.5' />
                        <span>Start Chat</span>
                      </Link>
                    </Button>
                  ) : (
                    <Button
                      variant='outline'
                      size='sm'
                      disabled
                      className='h-8 gap-1.5 opacity-50 w-full justify-center'
                    >
                      <MessageSquare className='size-3.5' />
                      <span>{doc.status === 'processing' ? 'Processing...' : 'Chat Unavailable'}</span>
                    </Button>
                  )}

                  {doc.status === 'failed' && onRetry && (
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={() => onRetry(doc)}
                      className='h-8 gap-1.5 border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 shrink-0'
                      title='Retry processing this document'
                    >
                      <RotateCw className='size-3.5' />
                      <span>Retry</span>
                    </Button>
                  )}

                  <Button
                    variant='ghost'
                    size='icon'
                    onClick={() => onDelete(doc)}
                    className='size-8 shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10'
                    aria-label={`Delete ${doc.filename}`}
                  >
                    <Trash2 className='size-4' />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </>
  )
}

