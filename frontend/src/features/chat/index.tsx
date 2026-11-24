import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from '@tanstack/react-router'
import {
  ArrowLeft,
  Loader2,
  Sparkles,
  FileQuestion,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { apiClient } from '@/api/client'
import { DocumentInfoCard } from './components/document-info-card'
import { ChatMessageItem } from './components/chat-message-item'
import { ChatInput } from './components/chat-input'
import { CitationSidePanel } from './components/citation-side-panel'
import type { DocumentDetail, Citation } from '@/api/types'
import type { ChatMessage } from './types'

interface ChatFeatureProps {
  documentId: string
}

const EXAMPLE_QUESTIONS = [
  'What are the main topics or concepts discussed in this document?',
  'Explain the core methodology or framework presented.',
  'What are the key conclusions, definitions, or findings?',
]

export function ChatFeature({ documentId }: ChatFeatureProps) {
  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [isLoadingDoc, setIsLoadingDoc] = useState(true)
  const [docError, setDocError] = useState<string | null>(null)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null)
  const [currentCitationsList, setCurrentCitationsList] = useState<Citation[]>([])
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  const scrollBottomRef = useRef<HTMLDivElement>(null)

  // Fetch document details on mount
  useEffect(() => {
    let isMounted = true
    setIsLoadingDoc(true)
    setDocError(null)

    apiClient
      .getDocument(documentId)
      .then((doc) => {
        if (isMounted) {
          setDocument(doc)
          if (doc.status !== 'ready') {
            setDocError(
              doc.status === 'processing'
                ? 'This document is still being indexed. Please wait until processing completes before chatting.'
                : 'This document failed ingestion. Please return to Documents and upload a valid PDF.'
            )
          }
        }
      })
      .catch((err) => {
        if (isMounted) {
          const msg =
            err.response?.status === 404
              ? 'Document not found. It may have been deleted.'
              : err.response?.data?.detail || err.message || 'Failed to load document.'
          setDocError(msg)
        }
      })
      .finally(() => {
        if (isMounted) setIsLoadingDoc(false)
      })

    return () => {
      isMounted = false
    }
  }, [documentId])

  // Auto-scroll to bottom whenever messages change or typing state changes
  useEffect(() => {
    scrollBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSendMessage = useCallback(
    async (questionText: string) => {
      if (!questionText.trim() || isTyping) return

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: questionText.trim(),
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMsg])
      setIsTyping(true)

      try {
        const response = await apiClient.askQuestion(documentId, questionText.trim())

        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          role: 'assistant',
          content: response.answer,
          citations: response.citations,
          found: response.found,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMsg])

        // Store citations list for the side panel navigation
        if (response.citations && response.citations.length > 0) {
          setCurrentCitationsList(response.citations)
        }
      } catch (err: any) {
        const errorDetail =
          err.response?.data?.detail ||
          err.message ||
          'Failed to retrieve answer. Please check backend connection.'

        const errorMsg: ChatMessage = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: errorDetail,
          isError: true,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setIsTyping(false)
      }
    },
    [documentId, isTyping]
  )

  const handleSelectCitation = (citation: Citation) => {
    setActiveCitation(citation)
  }

  // Handle retry for the last user message
  const handleRetryLastMessage = () => {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user')
    if (lastUserMessage) {
      handleSendMessage(lastUserMessage.content)
    }
  }

  // Document Loading State
  if (isLoadingDoc) {
    return (
      <div className='flex h-[calc(100vh-8rem)] items-center justify-center'>
        <div className='flex flex-col items-center gap-3 text-center'>
          <Loader2 className='size-8 animate-spin text-primary' />
          <p className='text-sm text-muted-foreground'>Loading document and verified index...</p>
        </div>
      </div>
    )
  }

  // Document Not Ready or Not Found Error State
  if (docError || !document) {
    return (
      <div className='flex h-[calc(100vh-8rem)] items-center justify-center p-4'>
        <Card className='max-w-md border-border/80 text-center p-6 shadow-sm'>
          <CardContent className='flex flex-col items-center gap-3 p-0'>
            <div className='flex size-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive'>
              <FileQuestion className='size-6' />
            </div>
            <h3 className='text-lg font-bold text-foreground'>Document Unavailable</h3>
            <p className='text-sm text-muted-foreground leading-relaxed'>
              {docError || 'We could not locate this document in your study library.'}
            </p>
            <Button asChild className='mt-2 gap-2'>
              <Link to='/documents'>
                <ArrowLeft className='size-4' />
                <span>Back to Documents</span>
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className='relative flex h-full w-full flex-1 min-h-0 overflow-hidden'>
      {/* 1. Left Column: Narrow Document Info Card */}
      <div
        className={`hidden lg:flex flex-col border-r border-border/80 bg-muted/15 p-4 transition-all duration-300 min-h-0 overflow-y-auto ${
          isSidebarCollapsed ? 'w-14 items-center p-2' : 'w-72 shrink-0'
        }`}
      >
        <div className='flex items-center justify-between w-full mb-3 shrink-0'>
          {!isSidebarCollapsed && (
            <span className='text-xs font-semibold uppercase tracking-wider text-muted-foreground'>
              Document
            </span>
          )}
          <Button
            variant='ghost'
            size='icon'
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className='size-7 text-muted-foreground hover:text-foreground'
            title={isSidebarCollapsed ? 'Expand document info' : 'Collapse document info'}
            aria-label='Toggle document info sidebar'
          >
            {isSidebarCollapsed ? (
              <ChevronRight className='size-4' />
            ) : (
              <ChevronLeft className='size-4' />
            )}
          </Button>
        </div>

        {!isSidebarCollapsed ? (
          <DocumentInfoCard document={document} />
        ) : (
          <Button variant='ghost' size='icon' asChild className='size-8 mt-2'>
            <Link to='/documents' title='Back to Documents'>
              <ArrowLeft className='size-4' />
            </Link>
          </Button>
        )}
      </div>

      {/* 2. Center Column: Chat Conversation Stream */}
      <div className='flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden bg-background'>
        {/* Chat Header for Mobile / Tablet */}
        <div className='shrink-0 flex items-center justify-between border-b border-border/80 px-4 py-2.5 bg-card/60 backdrop-blur-xs'>
          <div className='flex items-center gap-2.5 min-w-0'>
            <Button variant='ghost' size='sm' asChild className='lg:hidden -ml-2 size-8 p-0'>
              <Link to='/documents' aria-label='Back to documents'>
                <ArrowLeft className='size-4' />
              </Link>
            </Button>
            <div className='min-w-0'>
              <h2 className='text-sm font-semibold text-foreground truncate' title={document.filename}>
                {document.filename}
              </h2>
              <p className='text-[11px] text-muted-foreground'>
                {document.page_count} pages • Grounded AI Study Assistant
              </p>
            </div>
          </div>
        </div>

        {/* Message Stream with Full Vertical Scrolling */}
        <div className='flex-1 min-h-0 overflow-y-auto p-4 md:p-6 scroll-smooth'>
          <div className='mx-auto max-w-3xl space-y-4'>
            {/* Empty State */}
            {messages.length === 0 && (
              <div className='my-8 flex flex-col items-center justify-center text-center space-y-4'>
                <div className='flex size-14 items-center justify-center rounded-2xl bg-accent text-accent-foreground shadow-xs'>
                  <Sparkles className='size-7' />
                </div>
                <div className='max-w-md space-y-1.5'>
                  <h3 className='text-lg font-bold text-foreground'>
                    Ask Questions Grounded in Your PDF
                  </h3>
                  <p className='text-sm text-muted-foreground'>
                    Every answer is strictly synthesized from <strong>{document.filename}</strong> with clickable page citations.
                  </p>
                </div>

                <div className='w-full max-w-md pt-2 space-y-2'>
                  <p className='text-xs font-semibold uppercase tracking-wider text-muted-foreground'>
                    Suggested Questions
                  </p>
                  <div className='flex flex-col gap-2'>
                    {EXAMPLE_QUESTIONS.map((q, idx) => (
                      <button
                        key={idx}
                        type='button'
                        onClick={() => handleSendMessage(q)}
                        className='rounded-xl border border-border/80 bg-card p-3 text-left text-xs font-medium text-foreground hover:border-primary/40 hover:bg-accent/15 transition-all shadow-2xs cursor-pointer'
                      >
                        "{q}"
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Message List */}
            {messages.map((msg) => (
              <ChatMessageItem
                key={msg.id}
                message={msg}
                onSelectCitation={handleSelectCitation}
                onSuggestionClick={handleSendMessage}
                onRetry={msg.isError ? handleRetryLastMessage : undefined}
              />
            ))}

            {/* In-flight typing indicator */}
            {isTyping && (
              <div className='flex justify-start gap-2.5 my-3'>
                <div className='flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-2xs'>
                  <Sparkles className='size-4' />
                </div>
                <div className='rounded-2xl rounded-tl-xs border border-border/80 bg-card px-4 py-3 shadow-xs'>
                  <div className='flex items-center gap-2 text-xs text-muted-foreground'>
                    <Loader2 className='size-3.5 animate-spin text-primary' />
                    <span>Searching pages & synthesizing grounded answer...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={scrollBottomRef} />
          </div>
        </div>

        {/* Input Dock */}
        <div className='shrink-0 border-t border-border/80 bg-card/40 p-4 backdrop-blur-xs'>
          <div className='mx-auto max-w-3xl'>
            <ChatInput
              onSend={handleSendMessage}
              disabled={isTyping}
              placeholder={`Ask anything about "${document.filename}"...`}
            />
          </div>
        </div>
      </div>

      {/* 3. Right Column: Citation Side Panel (Sub-Step 5D) */}
      {activeCitation && (
        <CitationSidePanel
          citation={activeCitation}
          citations={currentCitationsList}
          onClose={() => setActiveCitation(null)}
          onNavigate={(nextCit) => setActiveCitation(nextCit)}
        />
      )}
    </div>
  )
}
