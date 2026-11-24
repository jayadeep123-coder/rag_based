import { type ImgHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export function Logo({ className, alt = 'AI Mentor Logo', ...props }: ImgHTMLAttributes<HTMLImageElement>) {
  return (
    <img
      src='/images/favicon.png'
      alt={alt}
      className={cn('size-6 rounded-md object-contain', className)}
      {...props}
    />
  )
}
