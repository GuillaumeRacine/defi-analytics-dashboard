import './globals.css'

export const metadata = {
  title: 'ETH Price Chart | 5-Year Daily Timeseries',
  description: 'Interactive ETH price visualization from DeFillama data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-900 text-white font-mono text-xs antialiased">
        {children}
      </body>
    </html>
  )
}