import { BookOpen, FileText } from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Learner',
    email: 'user@example.com',
    avatar: '',
  },
  teams: [
    {
      name: 'AI Mentor',
      logo: BookOpen,
      plan: 'Study & Interview RAG',
    },
  ],
  navGroups: [
    {
      title: 'Overview',
      items: [
        {
          title: 'Documents',
          url: '/documents',
          icon: FileText,
        },
      ],
    },
  ],
}
