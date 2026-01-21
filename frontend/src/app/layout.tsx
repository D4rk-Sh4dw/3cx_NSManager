import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Emergency Service Manager',
  description: 'Manage 3CX Call Routing',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
