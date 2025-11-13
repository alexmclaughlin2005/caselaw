/**
 * Dockets Browser Page
 *
 * Search and browse court dockets (cases)
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchDockets, DocketSearchParams, DocketListItem } from '../services/dockets'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { Badge } from '../components/ui/badge'
import { Search, ChevronLeft, ChevronRight, ExternalLink } from '../components/icons'
import { DocketDetailDrawer } from '../components/DocketDetailDrawer'

export default function Dockets() {
  const [searchParams, setSearchParams] = useState<DocketSearchParams>({
    page: 1,
    page_size: 50,
    sort_by: 'date_filed',
    sort_order: 'desc',
  })

  const [searchInput, setSearchInput] = useState('')
  const [selectedDocketId, setSelectedDocketId] = useState<number | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleDocketClick = (docketId: number) => {
    setSelectedDocketId(docketId)
    setDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setDrawerOpen(false)
    // Delay clearing the selected ID to allow drawer animation to complete
    setTimeout(() => setSelectedDocketId(null), 300)
  }

  // Query for dockets
  const { data, isLoading, error } = useQuery({
    queryKey: ['dockets', searchParams],
    queryFn: () => searchDockets(searchParams),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchParams({
      ...searchParams,
      q: searchInput || undefined,
      page: 1,
    })
  }

  const handlePageChange = (newPage: number) => {
    setSearchParams({ ...searchParams, page: newPage })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString()
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dockets</h1>
        <p className="text-gray-600 mt-2">
          Search and browse court cases from the CourtListener database
        </p>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle>Search Dockets</CardTitle>
          <CardDescription>
            Search by case name, docket number, or keywords. {data && `${data.total.toLocaleString()} total cases in database.`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search case name or docket number..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit">Search</Button>
            {searchParams.q && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setSearchInput('')
                  setSearchParams({ ...searchParams, q: undefined, page: 1 })
                }}
              >
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Results Card */}
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>
            {isLoading ? 'Loading...' : data ? (
              <>
                Showing {((data.page - 1) * data.page_size) + 1} - {Math.min(data.page * data.page_size, data.total)} of {data.total.toLocaleString()} dockets
                {searchParams.q && ` matching "${searchParams.q}"`}
              </>
            ) : null}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-red-500 p-4 border border-red-200 rounded">
              Error loading dockets: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <div className="text-gray-600">Loading dockets...</div>
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[200px]">Docket Number</TableHead>
                      <TableHead>Case Name</TableHead>
                      <TableHead className="w-[100px]">Court</TableHead>
                      <TableHead className="w-[120px]">Date Filed</TableHead>
                      <TableHead className="w-[100px]">Opinions</TableHead>
                      <TableHead className="w-[80px]">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.map((docket: DocketListItem) => (
                      <TableRow key={docket.id}>
                        <TableCell className="font-mono text-sm">
                          {docket.docket_number || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <button
                              onClick={() => handleDocketClick(docket.id)}
                              className="font-medium text-blue-600 hover:text-blue-800 hover:underline text-left transition-colors"
                            >
                              {docket.case_name || 'Unnamed Case'}
                            </button>
                            {docket.assigned_to_str && (
                              <div className="text-sm text-gray-600">
                                Judge: {docket.assigned_to_str}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{docket.court_id || 'N/A'}</Badge>
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatDate(docket.date_filed)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={docket.opinion_count > 0 ? 'default' : 'secondary'}>
                            {docket.opinion_count}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {docket.blocked ? (
                            <Badge variant="destructive">Blocked</Badge>
                          ) : docket.date_terminated ? (
                            <Badge variant="secondary">Terminated</Badge>
                          ) : (
                            <Badge variant="default">Active</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-600">
                  Page {data.page} of {data.total_pages.toLocaleString()}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(data.page - 1)}
                    disabled={!data.has_prev}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(data.page + 1)}
                    disabled={!data.has_next}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 text-gray-600">
              No dockets found. Try a different search query.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Docket Detail Drawer */}
      <DocketDetailDrawer
        docketId={selectedDocketId}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  )
}
