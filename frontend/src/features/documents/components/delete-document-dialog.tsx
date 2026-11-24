import { useState } from 'react'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { apiClient } from '@/api/client'
import { toast } from 'sonner'
import type { DocumentItem } from '@/api/types'

interface DeleteDocumentDialogProps {
  document: DocumentItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: (deletedId: string) => void
}

export function DeleteDocumentDialog({
  document,
  open,
  onOpenChange,
  onSuccess,
}: DeleteDocumentDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  if (!document) return null

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await apiClient.deleteDocument(document.id)
      toast.success(`"${document.filename}" deleted successfully.`)
      onOpenChange(false)
      onSuccess(document.id)
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Failed to delete document.'
      toast.error(`Delete failed: ${detail}`)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <ConfirmDialog
      open={open}
      onOpenChange={(val) => !isDeleting && onOpenChange(val)}
      title='Delete Document'
      desc={`Are you sure you want to delete "${document.filename}"? This will permanently delete the original PDF and all extracted vector chunks.`}
      confirmText='Delete Document'
      destructive
      isLoading={isDeleting}
      handleConfirm={handleDelete}
      className='sm:max-w-md'
    />
  )
}

