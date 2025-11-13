/**
 * Progress Bar Component
 */
interface ProgressBarProps {
  progress: number // 0.0 to 1.0
  label?: string
  showPercentage?: boolean
}

export const ProgressBar = ({ progress, label, showPercentage = true }: ProgressBarProps) => {
  const percentage = Math.round(progress * 100)
  
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showPercentage && (
            <span className="text-sm font-medium text-gray-700">{percentage}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

