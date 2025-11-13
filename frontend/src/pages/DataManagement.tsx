/**
 * Data Management Page
 * 
 * Allows users to download datasets from S3 and import them into the database.
 */
import { useState } from 'react'
import { useDatasets, useStartDownload, useDownloadStatus, useStartImport, useImportStatus, useDatabaseStatus, useImportProgress } from '../hooks/useDataManagement'
import { Button } from '../components/common/Button'
import { Card } from '../components/common/Card'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ProgressBar } from '../components/common/ProgressBar'
import type { DatasetInfo } from '../types/dataManagement'

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

export default function DataManagement() {
  const [selectedDate, setSelectedDate] = useState<string>('')
  
  // Queries
  const { data: datasetsData, isLoading: datasetsLoading, error: datasetsError } = useDatasets()
  const { data: databaseStatus, isLoading: dbStatusLoading } = useDatabaseStatus()
  const { data: importProgress, isLoading: importProgressLoading, refetch: refetchImportProgress } = useImportProgress()
  
  // Download
  const downloadMutation = useStartDownload()
  const { data: downloadStatus, isLoading: downloadStatusLoading } = useDownloadStatus(
    selectedDate,
    !!selectedDate
  )
  
  // Import
  const importMutation = useStartImport()
  const { data: importStatus, isLoading: importStatusLoading } = useImportStatus(
    selectedDate,
    !!selectedDate
  )
  
  // Get files for selected date
  const dateFiles = datasetsData?.datasets.filter(d => d.date === selectedDate) || []
  const csvFiles = dateFiles.filter(f => f.type === 'csv')
  const schemaFile = dateFiles.find(f => f.type === 'schema')
  
  const handleDownload = () => {
    if (!selectedDate) return
    
    downloadMutation.mutate({
      date: selectedDate,
      include_schema: true,
    })
  }
  
  const handleImport = () => {
    if (!selectedDate) return
    
    importMutation.mutate({
      date: selectedDate,
    })
  }
  
  // Group datasets by date
  const datasetsByDate = datasetsData?.dates.map(date => {
    const files = datasetsData.datasets.filter(d => d.date === date)
    return {
      date,
      files,
      csvCount: files.filter(f => f.type === 'csv').length,
      hasSchema: files.some(f => f.type === 'schema'),
    }
  }) || []
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Data Management</h1>
        <p className="mt-2 text-gray-600">
          Download datasets from CourtListener and import them into the database.
        </p>
      </div>
      
      {/* Database Status */}
      <Card title="Database Status" className="mb-6">
        {dbStatusLoading ? (
          <LoadingSpinner />
        ) : databaseStatus ? (
          <div className="space-y-6">
            {/* People Database */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">People Database</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_people.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">People</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_positions.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Positions</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_schools.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Schools</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_educations.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Education Records</div>
                </div>
              </div>
            </div>

            {/* Case Law Database */}
            <div className="pt-6 border-t">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Case Law Database</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_dockets.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Dockets</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_opinion_clusters.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Opinion Clusters</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_citations.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Citations</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {databaseStatus.total_parentheticals.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Parentheticals</div>
                </div>
              </div>
            </div>

            {databaseStatus.database_size_mb && (
              <div className="pt-4 border-t">
                <div className="text-sm text-gray-600">
                  Database Size: <span className="font-semibold">{databaseStatus.database_size_mb.toFixed(2)} MB</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-500">No data available</div>
        )}
      </Card>

      {/* Import Progress */}
      <Card title="Case Law Import Progress" className="mb-6">
        <div className="mb-4">
          <Button
            onClick={() => refetchImportProgress()}
            disabled={importProgressLoading}
            variant="secondary"
          >
            {importProgressLoading ? 'Refreshing...' : 'Refresh Progress'}
          </Button>
        </div>

        {importProgressLoading ? (
          <LoadingSpinner />
        ) : importProgress ? (
          <div className="space-y-6">
            {/* Helper function to render table progress */}
            {[
              { key: 'search_docket', label: 'search_docket', data: importProgress.search_docket },
              { key: 'search_opinioncluster', label: 'search_opinioncluster', data: importProgress.search_opinioncluster },
              { key: 'search_opinionscited', label: 'search_opinionscited', data: importProgress.search_opinionscited },
              { key: 'search_parenthetical', label: 'search_parenthetical', data: importProgress.search_parenthetical },
            ].map((table, index) => (
              <div key={table.key} className={index < 3 ? 'border-b pb-4' : 'pb-2'}>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-700">{table.label}</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    table.data.status === 'importing'
                      ? 'bg-blue-100 text-blue-800'
                      : table.data.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {table.data.status}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                  <div
                    className={`h-4 rounded-full transition-all duration-500 ${
                      table.data.status === 'completed'
                        ? 'bg-green-500'
                        : table.data.status === 'importing'
                        ? 'bg-blue-500'
                        : 'bg-gray-400'
                    }`}
                    style={{ width: `${table.data.progress_percent}%` }}
                  />
                </div>

                {/* Progress details */}
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">
                    {table.data.current_count.toLocaleString()} / {table.data.expected_count.toLocaleString()} rows
                  </span>
                  <span className="font-semibold text-gray-900">
                    {table.data.progress_percent.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500">No import progress data available</div>
        )}
      </Card>

      {/* Available Datasets */}
      <Card title="Available Datasets" className="mb-6">
        {datasetsLoading ? (
          <LoadingSpinner />
        ) : datasetsError ? (
          <div className="text-red-600">Error loading datasets: {String(datasetsError)}</div>
        ) : datasetsByDate.length === 0 ? (
          <div className="text-gray-500">No datasets available</div>
        ) : (
          <div className="space-y-4">
            {datasetsByDate.map(({ date, csvCount, hasSchema }) => (
              <div
                key={date}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedDate === date
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedDate(date)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-gray-900">{formatDate(date)}</div>
                    <div className="text-sm text-gray-600">
                      {csvCount} CSV files
                      {hasSchema && ' • Schema file'}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">{date}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
      
      {/* Selected Dataset Details */}
      {selectedDate && (
        <Card title={`Dataset: ${formatDate(selectedDate)}`} className="mb-6">
          <div className="space-y-4">
            {/* File List */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Files</h4>
              <div className="space-y-2">
                {schemaFile && (
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{schemaFile.key.split('/').pop()}</span>
                      <span className="ml-2 text-sm text-gray-600">Schema</span>
                    </div>
                    <span className="text-sm text-gray-600">{formatFileSize(schemaFile.size)}</span>
                  </div>
                )}
                {csvFiles.map((file) => (
                  <div key={file.key} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{file.table_name || file.key.split('/').pop()}</span>
                      <span className="ml-2 text-sm text-gray-600">CSV</span>
                    </div>
                    <span className="text-sm text-gray-600">{formatFileSize(file.size)}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Download Section */}
            <div className="pt-4 border-t">
              <h4 className="font-medium text-gray-900 mb-3">Download</h4>
              {downloadStatusLoading ? (
                <LoadingSpinner size="sm" />
              ) : downloadStatus ? (
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Status: <span className="capitalize">{downloadStatus.status}</span>
                      </span>
                    </div>
                    <ProgressBar progress={downloadStatus.progress} />
                  </div>
                  {downloadStatus.error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      Error: {downloadStatus.error}
                    </div>
                  )}
                  {downloadStatus.status === 'completed' && (
                    <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
                      Download completed successfully
                    </div>
                  )}
                </div>
              ) : null}
              
              <div className="mt-3">
                <Button
                  onClick={handleDownload}
                  disabled={downloadMutation.isPending || downloadStatus?.status === 'downloading'}
                  variant="primary"
                >
                  {downloadMutation.isPending || downloadStatus?.status === 'downloading' ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span className="ml-2">Downloading...</span>
                    </>
                  ) : (
                    'Download Dataset'
                  )}
                </Button>
              </div>
            </div>
            
            {/* Import Section */}
            <div className="pt-4 border-t">
              <h4 className="font-medium text-gray-900 mb-3">Import</h4>
              {importStatusLoading ? (
                <LoadingSpinner size="sm" />
              ) : importStatus ? (
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Status: <span className="capitalize">{importStatus.status}</span>
                      </span>
                      <span className="text-sm text-gray-600">
                        {importStatus.tables_completed.length} / {importStatus.tables_total} tables
                      </span>
                    </div>
                    <ProgressBar progress={importStatus.progress} />
                  </div>
                  
                  {importStatus.current_table && (
                    <div className="text-sm text-gray-600">
                      Currently importing: <span className="font-medium">{importStatus.current_table}</span>
                    </div>
                  )}
                  
                  {importStatus.tables_completed.length > 0 && (
                    <div className="text-sm text-gray-600">
                      Completed: {importStatus.tables_completed.join(', ')}
                    </div>
                  )}
                  
                  {importStatus.records_imported && Object.keys(importStatus.records_imported).length > 0 && (
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="font-medium">Records Imported:</div>
                      {Object.entries(importStatus.records_imported).map(([table, count]) => (
                        <div key={table} className="ml-4">
                          {table}: {count.toLocaleString()}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {importStatus.error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                      Error: {importStatus.error}
                    </div>
                  )}
                  
                  {importStatus.status === 'completed' && (
                    <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
                      Import completed successfully
                    </div>
                  )}
                </div>
              ) : null}
              
              <div className="mt-3">
                <Button
                  onClick={handleImport}
                  disabled={
                    importMutation.isPending ||
                    importStatus?.status === 'importing' ||
                    downloadStatus?.status !== 'completed'
                  }
                  variant="primary"
                >
                  {importMutation.isPending || importStatus?.status === 'importing' ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span className="ml-2">Importing...</span>
                    </>
                  ) : (
                    'Import Dataset'
                  )}
                </Button>
                {downloadStatus?.status !== 'completed' && (
                  <p className="mt-2 text-sm text-gray-500">
                    Please download the dataset first
                  </p>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

