import { createFileRoute } from '@tanstack/react-router'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'
import { ChatFeature } from '@/features/chat'

export const Route = createFileRoute('/_authenticated/chat/$documentId')({
  component: ChatRoute,
})

function ChatRoute() {
  const { documentId } = Route.useParams()

  return (
    <>
      <Header fixed>
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>
      <Main fixed fluid className='p-0 overflow-hidden h-[calc(100svh-4rem)]'>
        <ChatFeature documentId={documentId} />
      </Main>
    </>
  )
}
