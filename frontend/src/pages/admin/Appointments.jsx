import { useState, useEffect } from 'react'
import { getLeads } from '../../services/api.js'

export default function Appointments() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Define fetchAppointments (or loadAppointments) right here inside the component
  async function fetchAppointments() {
    try {
      setLoading(true)
      setError(null)
      const data = await getAppointments()
      setAppointments(data)
    } catch (err) {
      setError(err.message || 'Failed to load appointments.')
      setAppointments([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAppointments()
  }, [])

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Appointments</h3>
          <p className="text-muted small mb-0">Manage and review scheduled appointments.</p>
        </div>
        <button className="btn btn-outline-dark btn-sm" onClick={fetchAppointments}>
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
              <span className="text-muted">Loading appointments...</span>
            </div>
          ) : appointments.length === 0 ? (
            <div className="text-center py-5">
              <i className="bi bi-inbox display-4 text-muted mb-3"></i>
              <p className="text-muted mb-0">No appointments scheduled yet.</p>
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
                  {appointments.map((appointment) => (
                    <tr key={appointment.id}>
                      <td className="ps-4 fw-semibold">{appointment.name || 'N/A'}</td>
                      <td>{appointment.phone || 'N/A'}</td>
                      <td>{appointment.requested_service || 'N/A'}</td>
                      <td>{appointment.preferred_datetime || 'N/A'}</td>
                      <td>
                        <span className="badge bg-secondary bg-opacity-10 text-secondary border px-2 py-1">
                          {appointment.source || 'website_chat'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge px-2 py-1 ${appointment.status === 'new' ? 'bg-success bg-opacity-10 text-success border border-success' : 'bg-primary bg-opacity-10 text-primary'}`}>
                          {appointment.status || 'new'}
                        </span>
                      </td>
                      <td className="pe-4 text-muted small">
                        {appointment.created_at ? new Date(appointment.created_at).toLocaleString() : 'N/A'}
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