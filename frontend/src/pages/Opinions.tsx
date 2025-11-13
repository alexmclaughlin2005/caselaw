/**
 * Opinions Browser Page
 *
 * Search and browse legal opinions
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchOpinions, OpinionSearchParams, OpinionListItem } from '../services/opinions'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { Badge } from '../components/ui/badge'
import { Search, ChevronLeft, ChevronRight, TrendingUp } from '../components/icons'
import { OpinionDetailDrawer } from '../components/OpinionDetailDrawer'

export default function Opinions() {
  const [searchParams, setSearchParams] = useState<OpinionSearchParams>({
    page: 1,
    page_size: 50,
    sort_by: 'date_filed',
    sort_order: 'desc',
  })

  const [searchInput, setSearchInput] = useState('')
  const [selectedOpinionId, setSelectedOpinionId] = useState<number | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleOpinionClick = (opinionId: number) => {
    setSelectedOpinionId(opinionId)
    setDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setDrawerOpen(false)
    setTimeout(() => setSelectedOpinionId(null), 300)
  }

  // Query for opinions
  const { data, isLoading, error } = useQuery({
    queryKey: ['opinions', searchParams],
    queryFn: () => searchOpinions(searchParams),
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

  const handleSortByCitations = () => {
    setSearchParams({
      ...searchParams,
      sort_by: 'citation_count',
      sort_order: 'desc',
      page: 1,
    })
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString()
  }

  const getPrecedentialBadgeVariant = (status: string | null) => {
    if (!status) return 'secondary'
    if (status.toLowerCase().includes('published')) return 'default'
    if (status.toLowerCase().includes('unpublished')) return 'secondary'
    return 'outline'
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Opinions</h1>
        <p className="text-gray-600 mt-2">
          Search and browse legal opinions and judicial decisions
        </p>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle>Search Opinions</CardTitle>
          <CardDescription>
            Search by case name, judge names, or keywords. {data && `${data.total.toLocaleString()} total opinions in database.`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-3">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 h-4 w-4" />
                <Input
                  type="text"
                  placeholder="Search case name or judge..."
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
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleSortByCitations}
              >
                <TrendingUp className="h-4 w-4 mr-1" />
                Sort by Most Cited
              </Button>
            </div>
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
                Showing {((data.page - 1) * data.page_size) + 1} - {Math.min(data.page * data.page_size, data.total)} of {data.total.toLocaleString()} opinions
                {searchParams.q && ` matching "${searchParams.q}"`}
              </>
            ) : null}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-red-500 p-4 border border-red-200 rounded">
              Error loading opinions: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <div className="text-gray-600">Loading opinions...</div>
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Case Name</TableHead>
                      <TableHead className="w-[150px]">Judges</TableHead>
                      <TableHead className="w-[120px]">Date Filed</TableHead>
                      <TableHead className="w-[100px]">Citations</TableHead>
                      <TableHead className="w-[120px]">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.map((opinion: OpinionListItem) => (
                      <TableRow key={opinion.id}>
                        <TableCell>
                          <div className="space-y-1">
                            <button
                              onClick={() => handleOpinionClick(opinion.id)}
                              className="font-medium text-blue-600 hover:text-blue-800 hover:underline text-left transition-colors"
                            >
                              {opinion.case_name || 'Unnamed Case'}
                            </button>
                            {opinion.scdb_id && (
                              <div className="text-xs text-gray-600">
                                SCDB: {opinion.scdb_id}
                                {opinion.scdb_decision_direction && ` • ${opinion.scdb_decision_direction}`}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          <div className="truncate max-w-[150px]" title={opinion.judges || 'N/A'}>
                            {opinion.judges || 'N/A'}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatDate(opinion.date_filed)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={opinion.citation_count > 50 ? 'default' : 'secondary'}>
                            {opinion.citation_count}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getPrecedentialBadgeVariant(opinion.precedential_status)}>
                            {opinion.precedential_status || 'Unknown'}
                          </Badge>
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
              No opinions found. Try a different search query.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Opinion Detail Drawer */}
      <OpinionDetailDrawer
        opinionId={selectedOpinionId}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  )
}
