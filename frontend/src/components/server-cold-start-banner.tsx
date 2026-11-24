import { useEffect, useState, useRef } from 'react'
import { Loader2, Sparkles, X } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function ServerColdStartBanner() {
  const [isWakingUp, setIsWakingUp] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const isHealthyRef = useRef(false)

  useEffect(() => {
    let timer: number | null = null
    let pollInterval: number | null = null
    let isMounted = true

    const checkServerHealth = async () => {
      try {
        const source = axios.CancelToken.source()
        const timeoutId = window.setTimeout(() => {
          source.cancel('Health check timed out after 3 seconds')
          if (isMounted && !isHealthyRef.current) {
            setIsWakingUp(true)
          }
        }, 3000)

        const res = await axios.get(`${API_BASE_URL}/health`, {
          cancelToken: source.token,
        })
        window.clearTimeout(timeoutId)

        if (res.status === 200 && isMounted) {
          isHealthyRef.current = true
          setIsWakingUp(false)
          if (pollInterval) {
            window.clearInterval(pollInterval)
            pollInterval = null
          }
        }
      } catch {
        if (isMounted && !isHealthyRef.current) {
          setIsWakingUp(true)
        }
      }
    }

    // Trigger initial check
    checkServerHealth()

    // If server takes longer than 3s, poll every 3.5s until alive
    timer = window.setTimeout(() => {
      if (!isHealthyRef.current && isMounted) {
        setIsWakingUp(true)
        pollInterval = window.setInterval(async () => {
          try {
            const res = await axios.get(`${API_BASE_URL}/health`, { timeout: 4000 })
            if (res.status === 200 && isMounted) {
              isHealthyRef.current = true
              setIsWakingUp(false)
              if (pollInterval) {
                window.clearInterval(pollInterval)
                pollInterval = null
              }
            }
          } catch {
            // Keep waiting
          }
        }, 3500)
      }
    }, 3000)

    return () => {
      isMounted = false
      if (timer) window.clearTimeout(timer)
      if (pollInterval) window.clearInterval(pollInterval)
    }
  }, [])

  if (!isWakingUp || isDismissed) {
    return null
  }

  return (
    <div
      role='status'
      aria-live='polite'
      className='relative z-50 flex items-center justify-between border-b border-accent/40 bg-accent/25 px-4 py-2.5 text-xs md:text-sm font-medium text-foreground transition-all duration-300'
    >
      <div className='flex items-center gap-2.5 mx-auto'>
        <Loader2 className='size-4 animate-spin text-primary shrink-0' />
        <span className='flex items-center gap-1.5'>
          <Sparkles className='size-3.5 text-primary hidden sm:inline' />
          <span>Waking up the server, this can take up to a minute on the free plan...</span>
        </span>
      </div>

      <button
        type='button'
        onClick={() => setIsDismissed(true)}
        className='text-muted-foreground hover:text-foreground p-1 transition-colors'
        aria-label='Dismiss waking up notice'
      >
        <X className='size-3.5' />
      </button>
    </div>
  )
}
