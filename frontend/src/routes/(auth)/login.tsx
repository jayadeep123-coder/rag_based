import { useState } from 'react'
import { createFileRoute, redirect, useNavigate } from '@tanstack/react-router'
import { BookOpen, AlertCircle, Loader2, LogIn, UserPlus } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const Route = createFileRoute('/(auth)/login')({
  beforeLoad: async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session) {
      throw redirect({ to: '/documents' })
    }
  },
  component: LoginPage,
})

function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [infoMsg, setInfoMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setInfoMsg(null)

    if (!email || !password) {
      setErrorMsg('Please enter both email and password.')
      return
    }

    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) {
          setErrorMsg(error.message)
        } else {
          setInfoMsg('Account created! Please check your email for confirmation or sign in.')
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) {
          setErrorMsg(error.message)
        } else {
          navigate({ to: '/documents' })
        }
      }
    } catch (err: any) {
      setErrorMsg(err?.message || 'Authentication failed. Please verify credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='flex min-h-svh flex-col items-center justify-center bg-background p-6 md:p-10'>
      <div className='w-full max-w-sm md:max-w-md'>
        <div className='flex flex-col items-center gap-2 text-center mb-6'>
          <div className='flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md'>
            <BookOpen className='size-6' />
          </div>
          <h1 className='text-2xl font-bold tracking-tight text-foreground'>AI Mentor</h1>
          <p className='text-sm text-muted-foreground'>
            Grounded PDF study & interview prep with verified citations
          </p>
        </div>

        <Card className='border-border/60 shadow-sm'>
          <CardHeader className='pb-4'>
            <div className='flex border-b border-border pb-2'>
              <button
                type='button'
                onClick={() => { setIsSignUp(false); setErrorMsg(null); setInfoMsg(null); }}
                className={`flex-1 pb-2 text-sm font-medium border-b-2 transition-colors ${
                  !isSignUp
                    ? 'border-primary text-primary font-semibold'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Sign In
              </button>
              <button
                type='button'
                onClick={() => { setIsSignUp(true); setErrorMsg(null); setInfoMsg(null); }}
                className={`flex-1 pb-2 text-sm font-medium border-b-2 transition-colors ${
                  isSignUp
                    ? 'border-primary text-primary font-semibold'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Create Account
              </button>
            </div>
            <CardTitle className='text-lg mt-2'>
              {isSignUp ? 'Create your account' : 'Welcome back'}
            </CardTitle>
            <CardDescription>
              {isSignUp ? 'Enter your details below to get started' : 'Sign in to access your study documents'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {errorMsg && (
              <div className='mb-4 flex items-start rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive'>
                <AlertCircle className='size-4 mr-2 shrink-0 mt-0.5' />
                <span>{errorMsg}</span>
              </div>
            )}

            {infoMsg && (
              <div className='mb-4 rounded-lg border border-primary/20 bg-accent/20 p-3 text-sm text-accent-foreground'>
                {infoMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className='space-y-4'>
              <div className='space-y-1.5'>
                <Label htmlFor='email'>Email address</Label>
                <Input
                  id='email'
                  type='email'
                  placeholder='you@example.com'
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className='space-y-1.5'>
                <Label htmlFor='password'>Password</Label>
                <Input
                  id='password'
                  type='password'
                  placeholder='••••••••'
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                />
              </div>

              <Button type='submit' className='w-full' disabled={loading}>
                {loading ? (
                  <Loader2 className='size-4 animate-spin' />
                ) : isSignUp ? (
                  <>
                    <UserPlus className='size-4 mr-2' />
                    Create Account
                  </>
                ) : (
                  <>
                    <LogIn className='size-4 mr-2' />
                    Sign In
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
