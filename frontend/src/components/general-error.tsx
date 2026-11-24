import { Button } from '@/components/ui/button'

export function GeneralError({ error, reset }: { error?: Error; reset?: () => void }) {
  return (
    <div className='flex h-svh flex-col items-center justify-center bg-background px-4 text-center'>
      <h1 className='text-4xl font-bold text-destructive'>Something went wrong</h1>
      <p className='mt-2 text-sm text-muted-foreground'>
        {error?.message || 'An unexpected error occurred. Please try again.'}
      </p>
      {reset && (
        <div className='mt-6'>
          <Button onClick={reset}>Try Again</Button>
        </div>
      )}
    </div>
  )
}
