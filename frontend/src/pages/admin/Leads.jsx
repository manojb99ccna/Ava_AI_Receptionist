import { useState, useEffect } from 'react'
import { getLeads } from '../../services/api.js'

export default function Leads() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Define fetchLeads (or loadLeads) right here inside the component
  async function fetchLeads() {
    try {
      setLoading(true)
      setError(null)
      const data = await getLeads()
      setLeads(data)
    } catch (err) {
      setError(err.message || 'Failed to load leads.')
      setLeads([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeads()
  }, [])

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Captured Leads</h3>
          <p className="text-muted small mb-0">Manage and review potential client inquiries captured by Ava.</p>
        </div>
        <button className="btn btn-outline-dark btn-sm" onClick={fetchLeads}>
          <i className="bi bi-arrow-clockwise me-1"></i>Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-danger py-2 small" role="alert">
          <i className="bi bi-exclamation-triangle me-1"></i>{error}
        </div>
      )}

      <div className="card border-0 shadow-sm">
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary spinner-border-sm me-2" role="status"></div>
              <span className="text-muted">Loading leads...</span>
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-5">
              <i className="bi bi-inbox display-4 text-muted mb-3"></i>
              <p className="text-muted mb-0">No leads captured yet. Test your chat widget to generate some!</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light text-uppercase fs-7 text-muted">
                  <tr>
                    <th className="py-3 ps-4">Name</th>
                    <th className="py-3">Phone</th>
                    <th className="py-3">Service Interest</th>
                    <th className="py-3">Preferred Time</th>
                    <th className="py-3">Source</th>
                    <th className="py-3">Status</th>
                    <th className="py-3 pe-4">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id}>
                      <td className="ps-4 fw-semibold">{lead.name || 'N/A'}</td>
                      <td>{lead.phone || 'N/A'}</td>
                      <td>{lead.requested_service || 'N/A'}</td>
                      <td>{lead.preferred_datetime || 'N/A'}</td>
                      <td>
                        <span className="badge bg-secondary bg-opacity-10 text-secondary border px-2 py-1">
                          {lead.source || 'website_chat'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge px-2 py-1 ${lead.status === 'new' ? 'bg-success bg-opacity-10 text-success border border-success' : 'bg-primary bg-opacity-10 text-primary'}`}>
                          {lead.status || 'new'}
                        </span>
                      </td>
                      <td className="pe-4 text-muted small">
                        {lead.created_at ? new Date(lead.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  )
}