
import { useState, useEffect } from 'react'
import { getAppointments } from '../../services/api.js'

function getDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

export default function Appointments() {
  // Appointment data and API states
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Calendar states
  const [currentMonth, setCurrentMonth] = useState(() => {
    const today = new Date()
    return new Date(today.getFullYear(), today.getMonth(), 1)
  })

  const [selectedDate, setSelectedDate] = useState(() =>
    getDateKey(new Date())
  )

  // Fetch appointments from FastAPI
  async function fetchAppointments() {
    try {
      setLoading(true)
      setError(null)

      const data = await getAppointments()

      setAppointments(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Failed to load appointments.')
      setAppointments([])
    } finally {
      setLoading(false)
    }
  }

  // Load appointments when component opens
  useEffect(() => {
    fetchAppointments()
  }, [])

  // Calendar calculations
  const year = currentMonth.getFullYear()
  const month = currentMonth.getMonth()

  const monthName = currentMonth.toLocaleDateString('en-IN', {
    month: 'long',
    year: 'numeric'
  })

  const daysInMonth = new Date(year, month + 1, 0).getDate()

  // Monday = 0, Sunday = 6
  const firstDayOffset =
    (new Date(year, month, 1).getDay() + 6) % 7

  const calendarCells = [
    ...Array(firstDayOffset).fill(null),
    ...Array.from({ length: daysInMonth }, (_, index) => index + 1)
  ]

  // Get appointments for a particular day
  function getAppointmentsForDay(day) {
    const dateKey = getDateKey(new Date(year, month, day))

    return appointments.filter(appointment => {
      return (
        appointment.appointment_date?.slice(0, 10) === dateKey &&
        appointment.status !== 'cancelled'
      )
    })
  }

  // Get appointments for selected date
  const selectedAppointments = appointments.filter(appointment =>
    appointment.appointment_date?.slice(0, 10) === selectedDate
  )

  // Navigate between months
  function changeMonth(offset) {
    const nextMonth = new Date(year, month + offset, 1)

    setCurrentMonth(nextMonth)
    setSelectedDate(getDateKey(nextMonth))
  }

  // Return to current month and date
  function goToToday() {
    const today = new Date()

    setCurrentMonth(
      new Date(today.getFullYear(), today.getMonth(), 1)
    )

    setSelectedDate(getDateKey(today))
  }

  // Appointment status styling
  function getStatusClass(status) {
    if (status === 'confirmed') return 'bg-success'
    if (status === 'cancelled') return 'bg-danger'
    return 'bg-warning text-dark'
  }

  return (
    <>
      {/* Page heading */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Appointments</h3>
          <p className="text-muted small mb-0">
            View and manage scheduled appointments.
          </p>
        </div>

        <button
          className="btn btn-outline-dark btn-sm"
          onClick={fetchAppointments}
          disabled={loading}
        >
          <i className="bi bi-arrow-clockwise me-1"></i>
          Refresh
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="alert alert-danger py-2 small" role="alert">
          <i className="bi bi-exclamation-triangle me-1"></i>
          {error}
        </div>
      )}

      {/* Calendar */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body p-3 p-md-4">

          {/* Calendar header */}
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h5 className="fw-bold mb-1">{monthName}</h5>
              <small className="text-muted">
                Appointment calendar
              </small>
            </div>

            <div className="d-flex gap-2">
              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={goToToday}
              >
                Today
              </button>

              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={() => changeMonth(-1)}
                aria-label="Previous month"
              >
                <i className="bi bi-chevron-left"></i>
              </button>

              <button
                className="btn btn-outline-secondary btn-sm"
                onClick={() => changeMonth(1)}
                aria-label="Next month"
              >
                <i className="bi bi-chevron-right"></i>
              </button>
            </div>
          </div>

          {/* Weekday names */}
          <div
            className="mb-2"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, minmax(0, 1fr))'
            }}
          >
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
              <div
                key={day}
                className="text-center text-muted small fw-semibold py-2"
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar dates */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
              gap: '6px'
            }}
          >
            {calendarCells.map((day, index) => {
              if (day === null) {
                return <div key={`empty-${index}`}></div>
              }

              const dateKey = getDateKey(
                new Date(year, month, day)
              )

              const dayAppointments = getAppointmentsForDay(day)
              const isSelected = selectedDate === dateKey
              const isToday = getDateKey(new Date()) === dateKey

              return (
                <button
                  key={dateKey}
                  type="button"
                  onClick={() => setSelectedDate(dateKey)}
                  className={`btn text-start p-2 ${
                    isSelected ? 'btn-primary' : 'btn-light border'
                  }`}
                  style={{
                    minHeight: '75px',
                    borderRadius: '8px',
                    border: isToday && !isSelected
                      ? '2px solid #0d6efd'
                      : undefined
                  }}
                >
                  <div className="fw-semibold">{day}</div>

                  {dayAppointments.length > 0 && (
                    <div className="mt-2">
                      <span
                        className={`badge ${
                          isSelected
                            ? 'bg-light text-primary'
                            : 'bg-primary'
                        }`}
                        style={{ fontSize: '10px' }}
                      >
                        {dayAppointments.length} booked
                      </span>
                    </div>
                  )}
                </button>
              )
            })}
          </div>

          {/* Calendar legend */}
          <div className="d-flex flex-wrap gap-3 mt-4 small text-muted">
            <span>
              <i className="bi bi-circle-fill text-primary me-1"></i>
              Has appointments
            </span>

            <span>
              <i className="bi bi-circle-fill text-warning me-1"></i>
              Pending
            </span>

            <span>
              <i className="bi bi-circle-fill text-success me-1"></i>
              Confirmed
            </span>
          </div>
        </div>
      </div>

      {/* Selected date appointment list */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white border-0 py-3">
          <h5 className="fw-bold mb-1">
            Appointments for{' '}
            {new Date(selectedDate + 'T00:00:00').toLocaleDateString(
              'en-IN',
              {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
              }
            )}
          </h5>

          <small className="text-muted">
            {selectedAppointments.length} appointment(s)
          </small>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="text-center py-4">
              <div className="spinner-border spinner-border-sm text-primary me-2"></div>
              <span className="text-muted">
                Loading appointments...
              </span>
            </div>
          ) : selectedAppointments.length === 0 ? (
            <div className="text-center py-4">
              <i className="bi bi-calendar-x display-5 text-muted"></i>
              <p className="text-muted mt-3 mb-0">
                No appointments scheduled for this date.
              </p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Service</th>
                    <th>Time</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {selectedAppointments.map(appointment => (
                    <tr key={appointment.id}>
                      <td className="fw-semibold">
                        {appointment.name || 'N/A'}
                      </td>

                      <td>{appointment.phone || 'N/A'}</td>

                      <td>{appointment.service || 'N/A'}</td>

                      <td>
                        {appointment.appointment_date
                          ? new Date(
                              appointment.appointment_date
                            ).toLocaleTimeString('en-IN', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })
                          : 'N/A'}
                      </td>

                      <td>
                        <span
                          className={`badge ${getStatusClass(appointment.status)}`}
                        >
                          {appointment.status || 'pending'}
                        </span>
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