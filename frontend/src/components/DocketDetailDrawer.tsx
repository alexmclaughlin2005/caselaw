/**
 * Docket Detail Drawer Component
 *
 * Displays full docket details in a slide-out panel
 */
import { useQuery } from '@tanstack/react-query'
import { getDocket, getDocketOpinions } from '../services/dockets'
import { Drawer, DrawerSection, DrawerField } from './ui/drawer'
import { Badge } from './ui/badge'

interface DocketDetailDrawerProps {
  docketId: number | null
  open: boolean
  onClose: () => void
}

export const DocketDetailDrawer: React.FC<DocketDetailDrawerProps> = ({ docketId, open, onClose }) => {
  // Query for docket details
  const { data: docket, isLoading: isLoadingDocket } = useQuery({
    queryKey: ['docket', docketId],
    queryFn: () => getDocket(docketId!),
    enabled: !!docketId && open,
  })

  // Query for docket opinions
  const { data: opinions, isLoading: isLoadingOpinions } = useQuery({
    queryKey: ['docket-opinions', docketId],
    queryFn: () => getDocketOpinions(docketId!),
    enabled: !!docketId && open,
  })

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!docketId) return null

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={docket?.case_name || 'Loading...'}
    >
      {isLoadingDocket ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-600">Loading docket details...</div>
        </div>
      ) : docket ? (
        <div className="space-y-6">
          {/* Case Information */}
          <DrawerSection title="Case Information">
            <DrawerField label="Docket Number" value={docket.docket_number} />
            <DrawerField label="Case Name" value={docket.case_name} />
            {docket.case_name_short && (
              <DrawerField label="Short Name" value={docket.case_name_short} />
            )}
            {docket.case_name_full && (
              <DrawerField label="Full Name" value={docket.case_name_full} />
            )}
            <DrawerField
              label="Court"
              value={
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{docket.court_id}</Badge>
                </div>
              }
            />
            <DrawerField
              label="Status"
              value={
                docket.blocked ? (
                  <Badge variant="destructive">Blocked</Badge>
                ) : docket.date_terminated ? (
                  <Badge variant="secondary">Terminated</Badge>
                ) : (
                  <Badge variant="default">Active</Badge>
                )
              }
            />
          </DrawerSection>

          {/* Dates */}
          <DrawerSection title="Important Dates">
            <DrawerField label="Date Filed" value={formatDate(docket.date_filed)} />
            {docket.date_terminated && (
              <DrawerField label="Date Terminated" value={formatDate(docket.date_terminated)} />
            )}
            {docket.date_argued && (
              <DrawerField label="Date Argued" value={formatDate(docket.date_argued)} />
            )}
            {docket.date_reargued && (
              <DrawerField label="Date Reargued" value={formatDate(docket.date_reargued)} />
            )}
            {docket.date_cert_granted && (
              <DrawerField label="Cert Granted" value={formatDate(docket.date_cert_granted)} />
            )}
            {docket.date_cert_denied && (
              <DrawerField label="Cert Denied" value={formatDate(docket.date_cert_denied)} />
            )}
            {docket.date_last_filing && (
              <DrawerField label="Last Filing" value={formatDate(docket.date_last_filing)} />
            )}
          </DrawerSection>

          {/* Judges/Parties */}
          {(docket.assigned_to_str || docket.referred_to_str || docket.panel_str) && (
            <DrawerSection title="Judges & Panel">
              {docket.assigned_to_str && (
                <DrawerField label="Assigned To" value={docket.assigned_to_str} />
              )}
              {docket.referred_to_str && (
                <DrawerField label="Referred To" value={docket.referred_to_str} />
              )}
              {docket.panel_str && (
                <DrawerField label="Panel" value={docket.panel_str} />
              )}
            </DrawerSection>
          )}

          {/* Case Details */}
          {(docket.nature_of_suit || docket.cause || docket.jurisdiction_type || docket.jury_demand) && (
            <DrawerSection title="Case Details">
              {docket.nature_of_suit && (
                <DrawerField label="Nature of Suit" value={docket.nature_of_suit} />
              )}
              {docket.cause && (
                <DrawerField label="Cause" value={docket.cause} />
              )}
              {docket.jurisdiction_type && (
                <DrawerField label="Jurisdiction Type" value={docket.jurisdiction_type} />
              )}
              {docket.jury_demand && (
                <DrawerField label="Jury Demand" value={docket.jury_demand} />
              )}
            </DrawerSection>
          )}

          {/* Federal Docket Information */}
          {(docket.docket_number_core || docket.federal_dn_case_type || docket.federal_dn_judge_initials_assigned) && (
            <DrawerSection title="Federal Docket Information">
              {docket.docket_number_core && (
                <DrawerField label="Core Number" value={docket.docket_number_core} />
              )}
              {docket.federal_dn_case_type && (
                <DrawerField label="Case Type" value={docket.federal_dn_case_type} />
              )}
              {docket.federal_dn_judge_initials_assigned && (
                <DrawerField label="Judge Initials (Assigned)" value={docket.federal_dn_judge_initials_assigned} />
              )}
              {docket.federal_dn_office_code && (
                <DrawerField label="Office Code" value={docket.federal_dn_office_code} />
              )}
            </DrawerSection>
          )}

          {/* Opinions */}
          <DrawerSection title="Opinions">
            {isLoadingOpinions ? (
              <div className="text-sm text-gray-600">Loading opinions...</div>
            ) : opinions && opinions.opinions && opinions.opinions.length > 0 ? (
              <div className="space-y-3">
                {opinions.opinions.map((opinion: any) => (
                  <div key={opinion.id} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                    <div className="font-medium text-sm text-gray-900 mb-1">
                      {opinion.case_name || 'Unnamed Opinion'}
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      {opinion.date_filed && (
                        <div>Filed: {formatDate(opinion.date_filed)}</div>
                      )}
                      {opinion.judges && (
                        <div>Judges: {opinion.judges}</div>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        {opinion.precedential_status && (
                          <Badge variant="outline" className="text-xs">
                            {opinion.precedential_status}
                          </Badge>
                        )}
                        {opinion.citation_count > 0 && (
                          <Badge variant="secondary" className="text-xs">
                            {opinion.citation_count} citations
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-600">No opinions found for this docket</div>
            )}
          </DrawerSection>

          {/* Additional Metadata */}
          {(docket.mdl_status || docket.pacer_case_id || docket.slug) && (
            <DrawerSection title="Additional Information">
              {docket.mdl_status && (
                <DrawerField label="MDL Status" value={docket.mdl_status} />
              )}
              {docket.pacer_case_id && (
                <DrawerField label="PACER Case ID" value={docket.pacer_case_id} />
              )}
              {docket.slug && (
                <DrawerField label="Slug" value={docket.slug} />
              )}
              {docket.view_count !== null && docket.view_count !== undefined && (
                <DrawerField label="View Count" value={docket.view_count.toLocaleString()} />
              )}
            </DrawerSection>
          )}

          {/* System Dates */}
          {(docket.date_created || docket.date_modified) && (
            <DrawerSection title="System Information">
              {docket.date_created && (
                <DrawerField label="Date Created" value={formatDateTime(docket.date_created)} />
              )}
              {docket.date_modified && (
                <DrawerField label="Date Modified" value={formatDateTime(docket.date_modified)} />
              )}
              <DrawerField label="Docket ID" value={docket.id} />
            </DrawerSection>
          )}
        </div>
      ) : (
        <div className="py-12 text-gray-600">
          Docket not found
        </div>
      )}
    </Drawer>
  )
}
