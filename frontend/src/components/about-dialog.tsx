import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ExternalLink, Heart, ShieldCheck } from 'lucide-react'

interface AboutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AboutDialog({ open, onOpenChange }: AboutDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='sm:max-w-md'>
        <DialogHeader>
          <div className='flex items-center gap-2.5 mb-1'>
            <img src='/images/favicon.png' alt='AI Mentor' className='size-8 rounded-lg object-contain' />
            <div>
              <DialogTitle className='text-lg font-bold'>AI Mentor</DialogTitle>
              <p className='text-xs text-muted-foreground'>Study & Interview RAG Workspace</p>
            </div>
          </div>
          <DialogDescription className='text-xs leading-relaxed text-muted-foreground pt-1'>
            Grounded PDF study mentor providing factual answers backed by page-aware citations.
          </DialogDescription>
        </DialogHeader>

        <div className='space-y-4 py-2 text-xs'>
          {/* Stack Badges */}
          <div className='flex flex-wrap gap-1.5'>
            <Badge variant='outline' className='text-[11px] font-medium'>React 19</Badge>
            <Badge variant='outline' className='text-[11px] font-medium'>Vite</Badge>
            <Badge variant='outline' className='text-[11px] font-medium'>Tailwind v4</Badge>
            <Badge variant='outline' className='text-[11px] font-medium'>FastAPI</Badge>
            <Badge variant='outline' className='text-[11px] font-medium'>Supabase pgvector</Badge>
            <Badge variant='outline' className='text-[11px] font-medium'>Google Gemini</Badge>
          </div>

          {/* Template Credit (MIT License) */}
          <div className='rounded-lg border border-border/80 bg-muted/30 p-3 space-y-1.5'>
            <div className='flex items-center gap-1.5 text-xs font-semibold text-foreground'>
              <Heart className='size-3.5 text-rose-500 fill-rose-500' />
              <span>Open-Source Attribution</span>
            </div>
            <p className='text-muted-foreground text-[11px] leading-relaxed'>
              UI scaffold and admin components are based on the excellent open-source project{' '}
              <a
                href='https://github.com/satnaing/shadcn-admin'
                target='_blank'
                rel='noopener noreferrer'
                className='inline-flex items-center gap-1 font-semibold text-primary underline underline-offset-2 hover:opacity-80'
              >
                <span>satnaing/shadcn-admin</span>
                <ExternalLink className='size-2.5' />
              </a>{' '}
              licensed under the MIT License.
            </p>
          </div>

          {/* Privacy & Grounding */}
          <div className='flex items-center gap-2 text-[11px] text-muted-foreground'>
            <ShieldCheck className='size-3.5 text-emerald-600 shrink-0' />
            <span>Strict grounding: Answers synthesize only statements from uploaded PDF passages.</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
