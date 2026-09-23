import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface-base text-text-secondary">
      <h1 className="text-4xl font-bold text-text-tertiary">404</h1>
      <p className="mt-2 text-text-primary">Page not found</p>
      <Link to="/" className="mt-6 text-accent-primary hover:text-accent-soft transition-colors">
        Return to Home
      </Link>
    </div>
  )
}
