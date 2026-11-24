import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'

export function NotFoundError() {
  return (
    <div className='flex h-svh flex-col items-center justify-center bg-background px-4 text-center'>
      <h1 className='text-6xl font-bold text-primary'>404</h1>
      <p className='mt-4 text-xl font-semibold text-foreground'>Page Not Found</p>
      <p className='mt-2 text-sm text-muted-foreground'>
        The page you are looking for does not exist or has been moved.
      </p>
      <div className='mt-6'>
        <Button asChild>
          <Link to='/documents'>Back to Documents</Link>
        </Button>
      </div>
    </div>
  )
}
