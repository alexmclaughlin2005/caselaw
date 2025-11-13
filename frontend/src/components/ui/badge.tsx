import * as React from "react"

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'destructive'
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const variants = {
      default: "bg-blue-100 text-blue-800",
      secondary: "bg-gray-100 text-gray-800",
      outline: "border border-gray-300 bg-white text-gray-700",
      destructive: "bg-red-100 text-red-800"
    }

    return (
      <span
        ref={ref}
        className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${variants[variant]} ${className}`}
        {...props}
      />
    )
  }
)
