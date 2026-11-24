import { useEffect, useState } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SignOutDialog } from '@/components/sign-out-dialog'
import { supabase } from '@/lib/supabase'
import { LogOut, User } from 'lucide-react'

export function ProfileDropdown() {
  const [open, setOpen] = useState(false)
  const [userEmail, setUserEmail] = useState<string>('user@example.com')

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user?.email) {
        setUserEmail(session.user.email)
      }
    })
  }, [])

  const initials = userEmail.substring(0, 2).toUpperCase()

  return (
    <>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button variant='ghost' className='relative h-9 w-9 rounded-full ring-1 ring-border'>
            <Avatar className='h-9 w-9'>
              <AvatarFallback className='bg-primary/10 text-primary font-semibold text-xs'>
                {initials}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className='w-56' align='end' forceMount>
          <DropdownMenuLabel className='font-normal'>
            <div className='flex flex-col gap-1.5'>
              <p className='text-sm leading-none font-medium flex items-center gap-1.5'>
                <User className='size-3.5 text-muted-foreground' />
                Account
              </p>
              <p className='text-xs leading-none text-muted-foreground truncate font-mono'>
                {userEmail}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setOpen(true)} className='text-destructive focus:text-destructive cursor-pointer'>
            <LogOut className='size-4 mr-2' />
            Sign Out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <SignOutDialog open={open} onOpenChange={setOpen} />
    </>
  )
}
