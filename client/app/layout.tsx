import type { Metadata } from 'next'
import { Figtree, Noto_Sans } from 'next/font/google'
import './globals.css'

const figtree = Figtree({ 
  subsets: ['latin'],
  variable: '--font-figtree',
  display: 'swap',
})

const notoSans = Noto_Sans({ 
  subsets: ['latin'],
  variable: '--font-noto',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'BigTB6 - TB Diagnostic Tool',
  description: 'Real-time AI diagnostic assistant powered by Gemini Live for TB symptom assessment',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${figtree.variable} ${notoSans.variable}`}>
      <body>{children}</body>
    </html>
  )
}
