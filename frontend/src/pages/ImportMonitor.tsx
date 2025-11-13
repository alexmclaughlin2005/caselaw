/**
 * Import Monitor Page
 *
 * Real-time monitoring of database import progress
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getLiveImportStatus, getDatabaseCounts, getDatabaseActivity } from '../services/monitoring'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { RefreshCw, Database, Activity, Clock, TrendingUp } from '../components/icons'

export default function ImportMonitor() {
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Query for live import status (refreshes every 5 seconds if enabled)
  const { data: liveStatus, isLoading: progressLoading, refetch: refetchProgress } = useQuery({
    queryKey: ['live-import-status'],
    queryFn: getLiveImportStatus,
    refetchInterval: autoRefresh ? 5000 : false,
  })

  // Query for database counts
  const { data: counts, isLoading: countsLoading, refetch: refetchCounts } = useQuery({
    queryKey: ['database-counts'],
    queryFn: getDatabaseCounts,
    refetchInterval: autoRefresh ? 10000 : false,
  })

  // Query for database activity
  const { data: activity, isLoading: activityLoading, refetch: refetchActivity } = useQuery({
    queryKey: ['database-activity'],
    queryFn: getDatabaseActivity,
    refetchInterval: autoRefresh ? 5000 : false,
  })

  const handleRefreshAll = () => {
    refetchProgress()
    refetchCounts()
    refetchActivity()
  }

  // Calculate estimated time remaining
  const getEstimatedTimeRemaining = () => {
    if (!liveStatus) return 'Calculating...'

    const percentage = liveStatus.overall_percentage
    if (percentage === 0) return 'Not started'
    if (percentage >= 100) return 'Complete!'

    // Rough estimate: assume linear progress at current rate
    // This is a simplified calculation
    const remainingPercentage = 100 - percentage
    const estimatedMinutes = (remainingPercentage / percentage) * 120 // Assume 2 hours baseline

    if (estimatedMinutes < 60) {
      return `~${Math.round(estimatedMinutes)} minutes`
    } else {
      const hours = Math.floor(estimatedMinutes / 60)
      const minutes = Math.round(estimatedMinutes % 60)
      return `~${hours}h ${minutes}m`
    }
  }

  // Get display name for table
  const getTableDisplayName = (tableName: string) => {
    const names: Record<string, string> = {
      'people_db_court': 'Courts',
      'people_db_person': 'Judges/People',
      'search_docket': 'Dockets',
      'search_opinioncluster': 'Opinion Clusters',
      'search_opinionscited': 'Citations',
      'search_parenthetical': 'Parentheticals',
    }
    return names[tableName] || tableName
  }

  // Sort tables: people DB first, then caselaw
  const sortTables = (tables: Record<string, any>) => {
    const order = [
      'people_db_court',
      'people_db_person',
      'search_docket',
      'search_opinioncluster',
      'search_opinionscited',
      'search_parenthetical',
    ]
    return order.filter(name => tables[name]).map(name => [name, tables[name]])
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'importing':
        return 'bg-blue-500'
      default:
        return 'bg-gray-300'
    }
  }

  const getStatusVariant = (status: string): 'default' | 'secondary' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'importing':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Import Monitor</h1>
          <p className="text-gray-600 mt-2">
            Real-time monitoring of Railway database import progress
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefreshAll}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* Overall Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Overall Import Progress
          </CardTitle>
          <CardDescription>
            {liveStatus ? (
              <>
                {liveStatus.total_records.toLocaleString()} / {liveStatus.expected_total.toLocaleString()} records imported
                {' • '}
                Status: {liveStatus.import_status}
                {' • '}
                Active queries: {liveStatus.active_queries}
                {' • '}
                Estimated time remaining: {getEstimatedTimeRemaining()}
              </>
            ) : 'Loading...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {progressLoading ? (
            <div className="text-center py-8 text-gray-600">Loading progress...</div>
          ) : liveStatus ? (
            <div className="space-y-4">
              {/* Overall progress bar */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Total Progress</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {liveStatus.overall_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-6">
                  <div
                    className="bg-blue-600 h-6 rounded-full transition-all duration-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${Math.min(liveStatus.overall_percentage, 100)}%` }}
                  >
                    {liveStatus.overall_percentage > 5 && `${liveStatus.overall_percentage.toFixed(1)}%`}
                  </div>
                </div>
                <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
                  <span>{liveStatus.total_records.toLocaleString()} records</span>
                  <span>{(liveStatus.expected_total - liveStatus.total_records).toLocaleString()} remaining</span>
                </div>
              </div>

              {/* Individual table progress */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                {sortTables(liveStatus.tables).map(([tableName, tableProgress]) => (
                  <div key={tableName} className="border rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-medium text-gray-900">{getTableDisplayName(tableName)}</h3>
                        <Badge variant={getStatusVariant(tableProgress.status)} className="mt-1">
                          {tableProgress.status}
                        </Badge>
                      </div>
                      <span className="text-xl font-bold text-gray-900">
                        {tableProgress.percentage.toFixed(1)}%
                      </span>
                    </div>

                    <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                      <div
                        className={`${getStatusColor(tableProgress.status)} h-3 rounded-full transition-all duration-500`}
                        style={{ width: `${Math.min(tableProgress.percentage, 100)}%` }}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">Current:</span> {tableProgress.current.toLocaleString()}
                      </div>
                      <div>
                        <span className="font-medium">Expected:</span> {tableProgress.expected.toLocaleString()}
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium">Remaining:</span> {(tableProgress.expected - tableProgress.current).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Active Query Details */}
              {liveStatus.query_details && liveStatus.query_details.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Currently Importing</h4>
                  <div className="space-y-2">
                    {liveStatus.query_details.map((query) => (
                      <div key={query.pid} className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">Table: {query.table}</Badge>
                            <Badge variant="secondary">PID: {query.pid}</Badge>
                          </div>
                          <span className="text-xs text-gray-600">
                            <Clock className="inline h-3 w-3 mr-1" />
                            {query.duration}
                          </span>
                        </div>
                        <div className="text-gray-600 font-mono text-xs break-all">{query.query}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-red-500">Failed to load progress data</div>
          )}
        </CardContent>
      </Card>

      {/* Database Stats Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Database Statistics
          </CardTitle>
          <CardDescription>Current record counts and storage usage</CardDescription>
        </CardHeader>
        <CardContent>
          {countsLoading ? (
            <div className="text-center py-8 text-gray-600">Loading database stats...</div>
          ) : counts ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-blue-600 font-medium mb-1">Total Records</div>
                  <div className="text-2xl font-bold text-blue-900">
                    {counts.total_records.toLocaleString()}
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-sm text-green-600 font-medium mb-1">Database Size</div>
                  <div className="text-2xl font-bold text-green-900">{counts.database_size}</div>
                </div>
                {Object.entries(counts.counts).map(([table, count]) => (
                  <div key={table} className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 font-medium mb-1 truncate" title={table}>
                      {table.replace('search_', '')}
                    </div>
                    <div className="text-xl font-bold text-gray-900">{count.toLocaleString()}</div>
                    <div className="text-xs text-gray-500 mt-1">{counts.table_sizes[table]}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-red-500">Failed to load database stats</div>
          )}
        </CardContent>
      </Card>

      {/* Database Activity Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Database Activity
          </CardTitle>
          <CardDescription>Current connections and active queries</CardDescription>
        </CardHeader>
        <CardContent>
          {activityLoading ? (
            <div className="text-center py-8 text-gray-600">Loading activity...</div>
          ) : activity ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-sm text-purple-600 font-medium mb-1">Connections</div>
                  <div className="text-2xl font-bold text-purple-900">{activity.connection_count}</div>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="text-sm text-yellow-600 font-medium mb-1">Active Queries</div>
                  <div className="text-2xl font-bold text-yellow-900">{activity.active_queries}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 font-medium mb-1">Idle</div>
                  <div className="text-2xl font-bold text-gray-900">{activity.idle_connections}</div>
                </div>
              </div>

              {activity.active_query_details && activity.active_query_details.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Active Queries</h4>
                  <div className="space-y-2">
                    {activity.active_query_details.map((query) => (
                      <div key={query.pid} className="bg-gray-50 rounded p-3 text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <Badge variant="outline">PID: {query.pid}</Badge>
                          <span className="text-xs text-gray-500">
                            <Clock className="inline h-3 w-3 mr-1" />
                            {query.duration_seconds.toFixed(1)}s
                          </span>
                        </div>
                        <div className="text-gray-600 font-mono text-xs break-all">{query.query}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-red-500">Failed to load activity data</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
