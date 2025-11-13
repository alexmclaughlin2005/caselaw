/**
 * Opinion Detail Drawer Component
 *
 * Displays full opinion details in a slide-out panel
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getOpinion, getOpinionDocket } from '../services/opinions'
import { getCitationStats, getCitingOpinions, getCitedOpinions } from '../services/citations'
import { Drawer, DrawerSection, DrawerField } from './ui/drawer'
import { Badge } from './ui/badge'
import { ChevronDown, ChevronUp } from './icons'

interface OpinionDetailDrawerProps {
  opinionId: number | null
  open: boolean
  onClose: () => void
}

export const OpinionDetailDrawer: React.FC<OpinionDetailDrawerProps> = ({ opinionId, open, onClose }) => {
  const [showCitingCases, setShowCitingCases] = useState(false)
  const [showCitedCases, setShowCitedCases] = useState(false)
  // Query for opinion details
  const { data: opinion, isLoading: isLoadingOpinion } = useQuery({
    queryKey: ['opinion', opinionId],
    queryFn: () => getOpinion(opinionId!),
    enabled: !!opinionId && open,
  })

  // Query for associated docket
  const { data: docket, isLoading: isLoadingDocket } = useQuery({
    queryKey: ['opinion-docket', opinionId],
    queryFn: () => getOpinionDocket(opinionId!),
    enabled: !!opinionId && open,
  })

  // Query for citation stats
  const { data: citationStats, isLoading: isLoadingCitations } = useQuery({
    queryKey: ['citation-stats', opinionId],
    queryFn: () => getCitationStats(opinionId!),
    enabled: !!opinionId && open,
  })

  // Query for all citing opinions (loaded when expanded)
  const { data: citingOpinions, isLoading: isLoadingCitingOpinions } = useQuery({
    queryKey: ['citing-opinions', opinionId],
    queryFn: () => getCitingOpinions(opinionId!, 500),
    enabled: !!opinionId && open && showCitingCases,
  })

  // Query for all cited opinions (loaded when expanded)
  const { data: citedOpinions, isLoading: isLoadingCitedOpinions } = useQuery({
    queryKey: ['cited-opinions', opinionId],
    queryFn: () => getCitedOpinions(opinionId!, 500),
    enabled: !!opinionId && open && showCitedCases,
  })

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getPrecedentialBadgeVariant = (status: string | null): 'default' | 'secondary' | 'outline' => {
    if (!status) return 'secondary'
    if (status.toLowerCase().includes('published')) return 'default'
    return 'secondary'
  }

  if (!opinionId) return null

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={opinion?.case_name || 'Loading...'}
    >
      {isLoadingOpinion ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-600">Loading opinion details...</div>
        </div>
      ) : opinion ? (
        <div className="space-y-6">
          {/* Opinion Information */}
          <DrawerSection title="Opinion Information">
            <DrawerField label="Case Name" value={opinion.case_name} />
            {opinion.case_name_short && (
              <DrawerField label="Short Name" value={opinion.case_name_short} />
            )}
            {opinion.case_name_full && (
              <DrawerField label="Full Name" value={opinion.case_name_full} />
            )}
            <DrawerField
              label="Precedential Status"
              value={
                <Badge variant={getPrecedentialBadgeVariant(opinion.precedential_status)}>
                  {opinion.precedential_status || 'Unknown'}
                </Badge>
              }
            />
            <DrawerField
              label="Citation Count"
              value={
                <Badge variant={opinion.citation_count > 50 ? 'default' : 'secondary'}>
                  {opinion.citation_count} citations
                </Badge>
              }
            />
            <DrawerField
              label="Blocked"
              value={opinion.blocked ? <Badge variant="destructive">Yes</Badge> : <Badge variant="secondary">No</Badge>}
            />
          </DrawerSection>

          {/* Dates */}
          <DrawerSection title="Important Dates">
            <DrawerField label="Date Filed" value={formatDate(opinion.date_filed)} />
            {opinion.date_argued && (
              <DrawerField label="Date Argued" value={formatDate(opinion.date_argued)} />
            )}
            {opinion.date_reargued && (
              <DrawerField label="Date Reargued" value={formatDate(opinion.date_reargued)} />
            )}
            {opinion.date_reargument_denied && (
              <DrawerField label="Reargument Denied" value={formatDate(opinion.date_reargument_denied)} />
            )}
          </DrawerSection>

          {/* Judges & Attorneys */}
          {(opinion.judges || opinion.attorneys) && (
            <DrawerSection title="Judges & Attorneys">
              {opinion.judges && (
                <DrawerField label="Judges" value={opinion.judges} />
              )}
              {opinion.attorneys && (
                <DrawerField label="Attorneys" value={opinion.attorneys} />
              )}
            </DrawerSection>
          )}

          {/* Opinion Content */}
          {(opinion.syllabus || opinion.headnotes || opinion.summary || opinion.posture) && (
            <DrawerSection title="Opinion Content">
              {opinion.syllabus && (
                <DrawerField
                  label="Syllabus"
                  value={<div className="text-sm whitespace-pre-wrap">{opinion.syllabus}</div>}
                />
              )}
              {opinion.headnotes && (
                <DrawerField
                  label="Headnotes"
                  value={<div className="text-sm whitespace-pre-wrap">{opinion.headnotes}</div>}
                />
              )}
              {opinion.summary && (
                <DrawerField
                  label="Summary"
                  value={<div className="text-sm whitespace-pre-wrap">{opinion.summary}</div>}
                />
              )}
              {opinion.posture && (
                <DrawerField label="Posture" value={opinion.posture} />
              )}
              {opinion.nature_of_suit && (
                <DrawerField label="Nature of Suit" value={opinion.nature_of_suit} />
              )}
            </DrawerSection>
          )}

          {/* Supreme Court Database (SCDB) Information */}
          {(opinion.scdb_id || opinion.scdb_decision_direction || opinion.scdb_votes_majority) && (
            <DrawerSection title="Supreme Court Database">
              {opinion.scdb_id && (
                <DrawerField label="SCDB ID" value={opinion.scdb_id} />
              )}
              {opinion.scdb_decision_direction && (
                <DrawerField label="Decision Direction" value={opinion.scdb_decision_direction} />
              )}
              {opinion.scdb_votes_majority !== null && (
                <DrawerField label="Votes Majority" value={opinion.scdb_votes_majority} />
              )}
              {opinion.scdb_votes_minority !== null && (
                <DrawerField label="Votes Minority" value={opinion.scdb_votes_minority} />
              )}
            </DrawerSection>
          )}

          {/* Associated Docket */}
          <DrawerSection title="Associated Docket">
            {isLoadingDocket ? (
              <div className="text-sm text-gray-600">Loading docket...</div>
            ) : docket ? (
              <div className="space-y-2">
                <DrawerField label="Docket Number" value={docket.docket_number} />
                <DrawerField label="Case Name" value={docket.case_name} />
                <DrawerField label="Court" value={<Badge variant="outline">{docket.court_id}</Badge>} />
                {docket.date_filed && (
                  <DrawerField label="Date Filed" value={formatDate(docket.date_filed)} />
                )}
                {docket.assigned_to_str && (
                  <DrawerField label="Judge Assigned" value={docket.assigned_to_str} />
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-600">No docket information available</div>
            )}
          </DrawerSection>

          {/* Citation Statistics */}
          <DrawerSection title="Citation Statistics">
            {isLoadingCitations ? (
              <div className="text-sm text-gray-600">Loading citations...</div>
            ) : citationStats ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setShowCitingCases(!showCitingCases)}
                    className="p-3 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors text-left"
                  >
                    <div className="text-2xl font-bold text-blue-900">{citationStats.times_cited}</div>
                    <div className="text-xs text-blue-600 flex items-center justify-between">
                      <span>Times Cited (Click to view)</span>
                      {showCitingCases ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </div>
                  </button>
                  <button
                    onClick={() => setShowCitedCases(!showCitedCases)}
                    className="p-3 bg-green-50 rounded-md hover:bg-green-100 transition-colors text-left"
                  >
                    <div className="text-2xl font-bold text-green-900">{citationStats.times_citing}</div>
                    <div className="text-xs text-green-600 flex items-center justify-between">
                      <span>Times Citing (Click to view)</span>
                      {showCitedCases ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </div>
                  </button>
                </div>

                {/* Expanded: Cases Citing This Opinion */}
                {showCitingCases && (
                  <div className="border border-blue-200 rounded-md p-4 bg-blue-50/50">
                    <div className="text-sm font-medium text-gray-900 mb-3">
                      Cases Citing This Opinion ({citationStats.times_cited})
                    </div>
                    {isLoadingCitingOpinions ? (
                      <div className="text-sm text-gray-600">Loading citing cases...</div>
                    ) : citingOpinions && citingOpinions.citing_opinions && citingOpinions.citing_opinions.length > 0 ? (
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {citingOpinions.citing_opinions.map((cite: any) => (
                          <div key={cite.id} className="p-3 bg-white rounded border border-gray-200">
                            <div className="font-medium text-sm text-gray-900 mb-1">
                              {cite.citing_case_name || 'Unnamed Case'}
                            </div>
                            <div className="text-xs text-gray-600 space-y-1">
                              {cite.citing_date_filed && (
                                <div>Filed: {formatDate(cite.citing_date_filed)}</div>
                              )}
                              <div className="flex items-center gap-2 mt-1">
                                {cite.citing_citation_count > 0 && (
                                  <Badge variant="secondary" className="text-xs">
                                    {cite.citing_citation_count} citations
                                  </Badge>
                                )}
                                {cite.depth !== null && (
                                  <Badge variant="outline" className="text-xs">
                                    Depth: {cite.depth}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-600">No citing cases found</div>
                    )}
                  </div>
                )}

                {/* Expanded: Cases Cited By This Opinion */}
                {showCitedCases && (
                  <div className="border border-green-200 rounded-md p-4 bg-green-50/50">
                    <div className="text-sm font-medium text-gray-900 mb-3">
                      Cases Cited By This Opinion ({citationStats.times_citing})
                    </div>
                    {isLoadingCitedOpinions ? (
                      <div className="text-sm text-gray-600">Loading cited cases...</div>
                    ) : citedOpinions && citedOpinions.cited_opinions && citedOpinions.cited_opinions.length > 0 ? (
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {citedOpinions.cited_opinions.map((cite: any) => (
                          <div key={cite.id} className="p-3 bg-white rounded border border-gray-200">
                            <div className="font-medium text-sm text-gray-900 mb-1">
                              {cite.cited_case_name || 'Unnamed Case'}
                            </div>
                            <div className="text-xs text-gray-600 space-y-1">
                              {cite.cited_date_filed && (
                                <div>Filed: {formatDate(cite.cited_date_filed)}</div>
                              )}
                              <div className="flex items-center gap-2 mt-1">
                                {cite.cited_citation_count > 0 && (
                                  <Badge variant="secondary" className="text-xs">
                                    {cite.cited_citation_count} citations
                                  </Badge>
                                )}
                                {cite.depth !== null && (
                                  <Badge variant="outline" className="text-xs">
                                    Depth: {cite.depth}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-sm text-gray-600">No cited cases found</div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-600">No citation data available</div>
            )}
          </DrawerSection>

          {/* Additional Information */}
          <DrawerSection title="Additional Information">
            {opinion.source && (
              <DrawerField label="Source" value={opinion.source} />
            )}
            {opinion.slug && (
              <DrawerField label="Slug" value={opinion.slug} />
            )}
            <DrawerField label="Opinion ID" value={opinion.id} />
            <DrawerField label="Docket ID" value={opinion.docket_id} />
          </DrawerSection>
        </div>
      ) : (
        <div className="py-12 text-gray-600">
          Opinion not found
        </div>
      )}
    </Drawer>
  )
}
