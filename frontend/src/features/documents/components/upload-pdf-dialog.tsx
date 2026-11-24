import { useState, useRef, useCallback } from 'react'
import { UploadCloud, FileText, AlertCircle, Loader2, X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/api/client'
import { toast } from 'sonner'
import type { DocumentItem } from '@/api/types'

interface UploadPdfDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: (newDoc: DocumentItem) => void
}

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 // 10 MB

export function UploadPdfDialog({ open, onOpenChange, onSuccess }: UploadPdfDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateAndSetFile = (selectedFile: File) => {
    setErrorMsg(null)

    // 1. Validate file extension and MIME type
    const isPdfType = selectedFile.type === 'application/pdf'
    const isPdfExt = selectedFile.name.toLowerCase().endsWith('.pdf')
    if (!isPdfType && !isPdfExt) {
      setErrorMsg('Invalid file type. Only PDF documents (.pdf) are supported.')
      return
    }

    // 2. Validate file size (max 10 MB)
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      const sizeMb = (selectedFile.size / (1024 * 1024)).toFixed(2)
      setErrorMsg(`File size (${sizeMb} MB) exceeds the maximum allowed limit of 10 MB.`)
      return
    }

    if (selectedFile.size === 0) {
      setErrorMsg('The selected PDF file is empty (0 bytes).')
      return
    }

    setFile(selectedFile)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setErrorMsg(null)

    try {
      const newDoc = await apiClient.uploadDocument(file)
      toast.success(`"${file.name}" uploaded successfully! Ingestion in progress.`)
      setFile(null)
      onOpenChange(false)
      onSuccess(newDoc)
    } catch (err: any) {
      let detail =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        'Failed to upload PDF. Please check backend connection.'
      if (err.code === 'ERR_NETWORK' || !err.response) {
        detail = 'Server is waking up or temporarily unreachable. Please wait a moment and try again.'
      }
      setErrorMsg(detail)
      toast.error(`Upload failed: ${detail}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleClose = (newOpen: boolean) => {
    if (isUploading) return // Prevent closing while upload is in progress
    if (!newOpen) {
      setFile(null)
      setErrorMsg(null)
    }
    onOpenChange(newOpen)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className='sm:max-w-md bg-card border-border'>
        <DialogHeader>
          <DialogTitle className='text-lg font-semibold text-foreground'>Upload PDF Document</DialogTitle>
          <DialogDescription className='text-muted-foreground text-sm'>
            Upload a study guide, textbook, or notes (max 10 MB). Text will be extracted, chunked, and indexed for grounded Q&A.
          </DialogDescription>
        </DialogHeader>

        {errorMsg && (
          <div className='flex items-start gap-2.5 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive'>
            <AlertCircle className='size-4 shrink-0 mt-0.5' />
            <span className='leading-tight'>{errorMsg}</span>
          </div>
        )}

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !file && !isUploading && fileInputRef.current?.click()}
          className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-all ${
            isDragging
              ? 'border-primary bg-accent/20 cursor-copy'
              : file
              ? 'border-border/80 bg-accent/10'
              : 'border-border/80 hover:border-primary/50 hover:bg-muted/30 cursor-pointer'
          }`}
        >
          <input
            ref={fileInputRef}
            type='file'
            accept='application/pdf'
            className='hidden'
            onChange={handleFileChange}
            disabled={isUploading}
          />

          {!file ? (
            <div className='flex flex-col items-center gap-2 py-4'>
              <div className='flex size-12 items-center justify-center rounded-full bg-accent/30 text-accent-foreground'>
                <UploadCloud className='size-6' />
              </div>
              <div className='text-sm'>
                <span className='font-semibold text-primary'>Click to browse</span> or drag and drop
              </div>
              <p className='text-xs text-muted-foreground'>PDF only (standard text, up to 20 MB)</p>
            </div>
          ) : (
            <div className='flex w-full items-center justify-between gap-3 p-2'>
              <div className='flex items-center gap-3 min-w-0'>
                <div className='flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary'>
                  <FileText className='size-5' />
                </div>
                <div className='text-left min-w-0'>
                  <p className='truncate text-sm font-medium text-foreground'>{file.name}</p>
                  <p className='text-xs text-muted-foreground'>{formatFileSize(file.size)}</p>
                </div>
              </div>
              {!isUploading && (
                <Button
                  type='button'
                  variant='ghost'
                  size='icon'
                  className='size-8 shrink-0 text-muted-foreground hover:text-foreground'
                  onClick={(e) => {
                    e.stopPropagation()
                    setFile(null)
                    setErrorMsg(null)
                  }}
                  aria-label='Remove file'
                >
                  <X className='size-4' />
                </Button>
              )}
            </div>
          )}
        </div>

        {isUploading && (
          <div className='space-y-1.5 pt-1'>
            <div className='flex items-center justify-between text-xs text-muted-foreground'>
              <span className='flex items-center gap-1.5'>
                <Loader2 className='size-3.5 animate-spin text-primary' />
                Uploading and verifying PDF header...
              </span>
            </div>
            <div className='h-1.5 w-full overflow-hidden rounded-full bg-muted'>
              <div className='h-full w-2/3 animate-pulse rounded-full bg-primary' />
            </div>
          </div>
        )}

        <DialogFooter className='gap-2 sm:gap-0 pt-2'>
          <Button
            type='button'
            variant='outline'
            onClick={() => handleClose(false)}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            type='button'
            onClick={handleUpload}
            disabled={!file || isUploading}
            className='gap-2'
          >
            {isUploading ? (
              <>
                <Loader2 className='size-4 animate-spin' />
                Uploading...
              </>
            ) : (
              <>
                <UploadCloud className='size-4' />
                Start Ingestion
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

