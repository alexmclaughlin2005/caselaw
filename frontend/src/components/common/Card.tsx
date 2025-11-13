/**
 * Card Component
 */
import { HTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('bg-white rounded-lg shadow-md p-6', className)}
        {...props}
      >
        {title && (
          <h3 className="text-lg font-semibold mb-4 text-gray-900">{title}</h3>
        )}
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

