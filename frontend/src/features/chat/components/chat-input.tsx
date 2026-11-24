import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  onSend: (question: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about this document...',
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  return (
    <div className='relative rounded-xl border border-border/80 bg-card p-2 shadow-xs transition-colors focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20'>
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className='min-h-[44px] max-h-[180px] w-full resize-none border-0 bg-transparent p-2 text-sm shadow-none focus-visible:ring-0 focus-visible:outline-hidden placeholder:text-muted-foreground'
      />
      <div className='flex items-center justify-between border-t border-border/50 pt-2 px-1'>
        <span className='text-[11px] text-muted-foreground'>
          <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for new line
        </span>
        <Button
          type='button'
          size='sm'
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          className='size-8 p-0 rounded-lg'
          aria-label='Send message'
        >
          {disabled ? (
            <Loader2 className='size-4 animate-spin' />
          ) : (
            <Send className='size-4' />
          )}
        </Button>
      </div>
    </div>
  )
}

