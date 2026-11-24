import { useState, useEffect, useRef, useCallback } from 'react'
import { Plus, UploadCloud, RefreshCw, AlertCircle, Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient } from '@/api/client'
import { toast } from 'sonner'
import { DocumentTable } from './components/document-table'
import { UploadPdfDialog } from './components/upload-pdf-dialog'
import { DeleteDocumentDialog } from './components/delete-document-dialog'
import type { DocumentItem } from '@/api/types'

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [deleteDoc, setDeleteDoc] = useState<DocumentItem | null>(null)

  const pollingRef = useRef<number | null>(null)

  const fetchDocuments = useCallback(async (isPolling = false) => {
    if (!isPolling) setFetchError(null)
    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs)
    } catch (err: any) {
      if (!isPolling) {
        const msg = err.response?.data?.detail || err.message || 'Failed to fetch documents.'
        setFetchError(msg)
      }
    } finally {
      if (!isPolling) setIsLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchDocuments(false)
  }, [fetchDocuments])

  // Polling effect: Poll every 3 seconds ONLY while at least one document is processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === 'processing' || d.status === 'uploaded'
    )

    if (hasProcessing) {
      if (!pollingRef.current) {
        pollingRef.current = window.setInterval(() => {
          fetchDocuments(true)
        }, 3000)
      }
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [documents, fetchDocuments])

  const handleUploadSuccess = (newDoc: DocumentItem) => {
    // Optimistically prepend new doc or trigger refresh
    setDocuments((prev) => [newDoc, ...prev.filter((d) => d.id !== newDoc.id)])
    // Polling will automatically trigger because status is 'processing'
  }

  const handleDeleteSuccess = (deletedId: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== deletedId))
    setDeleteDoc(null)
  }

  const handleRetry = async (doc: DocumentItem) => {
    try {
      const updated = await apiClient.retryDocument(doc.id)
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? updated : d)))
      toast.success(`Retrying ingestion for "${doc.filename}"...`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to retry ingestion. Please check connection.')
    }
  }

  return (
    <div className='space-y-6'>
      {/* Page Header */}
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h2 className='text-2xl font-bold tracking-tight text-foreground'>Documents</h2>
          <p className='text-sm text-muted-foreground'>
            Upload and manage your study materials for grounded RAG Q&A
          </p>
        </div>
        <div className='flex items-center gap-2'>
          <Button
            onClick={() => setIsUploadOpen(true)}
            className='gap-2 shadow-xs'
          >
            <Plus className='size-4' />
            <span>Upload PDF</span>
          </Button>
        </div>
      </div>

      {/* Error State */}
      {fetchError && (
        <Card className='border-destructive/20 bg-destructive/10'>
          <CardContent className='flex items-center justify-between p-4'>
            <div className='flex items-center gap-3'>
              <AlertCircle className='size-5 text-destructive shrink-0' />
              <div>
                <p className='font-semibold text-sm text-destructive'>Error loading documents</p>
                <p className='text-xs text-muted-foreground'>{fetchError}</p>
              </div>
            </div>
            <Button
              variant='outline'
              size='sm'
              onClick={() => {
                setIsLoading(true)
                fetchDocuments(false)
              }}
              className='gap-1.5'
            >
              <RefreshCw className='size-3.5' />
              <span>Retry</span>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className='rounded-xl border border-border/80 bg-card p-6 space-y-4'>
          <div className='flex items-center justify-between'>
            <Skeleton className='h-6 w-32' />
            <Skeleton className='h-8 w-24' />
          </div>
          <div className='space-y-3 pt-2'>
            <Skeleton className='h-12 w-full rounded-lg' />
            <Skeleton className='h-12 w-full rounded-lg' />
            <Skeleton className='h-12 w-full rounded-lg' />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !fetchError && documents.length === 0 && (
        <Card className='border-dashed border-2 border-border/80 bg-card/50'>
          <CardContent className='flex flex-col items-center justify-center py-16 text-center space-y-4'>
            <div className='flex size-16 items-center justify-center rounded-2xl bg-accent/30 text-accent-foreground'>
              <Layers className='size-8' />
            </div>
            <div className='space-y-1.5 max-w-sm'>
              <h3 className='text-lg font-semibold text-foreground'>
                Upload your first PDF to get started
              </h3>
              <p className='text-sm text-muted-foreground'>
                Upload lecture slides, textbooks, or interview guides (up to 10 MB). Our AI Mentor indexes each page with verified citations.
              </p>
            </div>
            <Button
              onClick={() => setIsUploadOpen(true)}
              className='gap-2 mt-2'
            >
              <UploadCloud className='size-4' />
              <span>Upload PDF</span>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Documents List (Table on desktop, Cards on mobile) */}
      {!isLoading && !fetchError && documents.length > 0 && (
        <DocumentTable
          documents={documents}
          onDelete={(doc) => setDeleteDoc(doc)}
          onRetry={handleRetry}
        />
      )}

      {/* Upload Dialog */}
      <UploadPdfDialog
        open={isUploadOpen}
        onOpenChange={setIsUploadOpen}
        onSuccess={handleUploadSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteDocumentDialog
        document={deleteDoc}
        open={!!deleteDoc}
        onOpenChange={(open) => !open && setDeleteDoc(null)}
        onSuccess={handleDeleteSuccess}
      />
    </div>
  )
}
