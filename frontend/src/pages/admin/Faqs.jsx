import { useState, useEffect } from 'react'
import { getFaqs, createFaq, updateFaq, deleteFaq } from '../../services/api.js'

export default function Faqs() {
  const [faqs, setFaqs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Modal / Form state
  const [showModal, setShowModal] = useState(false)
  const [editingFaq, setEditingFaq] = useState(null)
  const [formData, setFormData] = useState({ intent: '', question: '', answer: '', is_active: true })

  useEffect(() => {
    loadFaqs()
  }, [])

  async function loadFaqs() {
    try {
      setLoading(true)
      setError(null)
      const data = await getFaqs()
      setFaqs(data)
    } catch (err) {
      setError(err.message || 'Failed to load FAQs.')
    } finally {
      setLoading(false)
    }
  }

  function handleOpenCreate() {
    setEditingFaq(null)
    setFormData({ intent: '', question: '', answer: '', is_active: true })
    setShowModal(true)
  }

  function handleOpenEdit(faq) {
    setEditingFaq(faq)
    setFormData({ intent: faq.intent, question: faq.question, answer: faq.answer, is_active: faq.is_active })
    setShowModal(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editingFaq) {
        await updateFaq(editingFaq.id, formData)
      } else {
        await createFaq(formData)
      }
      setShowModal(false)
      loadFaqs()
    } catch (err) {
      alert(err.message || 'Failed to save FAQ.')
    }
  }

  async function handleDelete(id) {
    if (!confirm('Are you sure you want to delete this FAQ?')) return
    try {
      await deleteFaq(id)
      loadFaqs()
    } catch (err) {
      alert(err.message || 'Failed to delete FAQ.')
    }
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Business FAQs & Knowledge Base</h3>
          <p className="text-muted small mb-0">Manage what Ava knows and how she answers visitor questions.</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleOpenCreate}>
          <i className="bi bi-plus-lg me-1"></i>Add New FAQ
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
              <span className="text-muted">Loading knowledge base...</span>
            </div>
          ) : faqs.length === 0 ? (
            <div className="text-center py-5">
              <i className="bi bi-question-circle display-4 text-muted mb-3"></i>
              <p className="text-muted mb-0">No FAQs found. Add your first business question and answer!</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead className="table-light text-uppercase fs-7 text-muted">
                  <tr>
                    <th className="py-3 ps-4">Intent</th>
                    <th className="py-3">Question</th>
                    <th className="py-3">Answer</th>
                    <th className="py-3">Status</th>
                    <th className="py-3 text-end pe-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {faqs.map((faq) => (
                    <tr key={faq.id}>
                      <td className="ps-4 fw-semibold">
                        <span className="badge bg-dark bg-opacity-10 text-dark border px-2 py-1">
                          {faq.intent}
                        </span>
                      </td>
                      <td style={{ maxWidth: '250px' }} className="text-truncate">{faq.question}</td>
                      <td style={{ maxWidth: '350px' }} className="text-truncate text-muted">{faq.answer}</td>
                      <td>
                        <span className={`badge ${faq.is_active ? 'bg-success bg-opacity-10 text-success border border-success' : 'bg-secondary bg-opacity-10 text-secondary'}`}>
                          {faq.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="text-end pe-4">
                        <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => handleOpenEdit(faq)}>
                          <i className="bi bi-pencil"></i>
                        </button>
                        <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(faq.id)}>
                          <i className="bi bi-trash"></i>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content border-0 shadow">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">{editingFaq ? 'Edit FAQ' : 'Add New FAQ'}</h5>
                <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Intent Name</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. pricing, services, hours"
                      value={formData.intent} 
                      onChange={(e) => setFormData({ ...formData, intent: e.target.value })}
                      required 
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Visitor Question</label>
                    <textarea 
                      className="form-control" 
                      rows="2"
                      placeholder="How much do your services cost?"
                      value={formData.question} 
                      onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                      required 
                    ></textarea>
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Ava's Approved Answer</label>
                    <textarea 
                      className="form-control" 
                      rows="3"
                      placeholder="Our pricing varies..."
                      value={formData.answer} 
                      onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                      required 
                    ></textarea>
                  </div>
                  <div className="form-check">
                    <input 
                      type="checkbox" 
                      className="form-check-input" 
                      id="isActiveCheck"
                      checked={formData.is_active} 
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    <label className="form-check-label small fw-semibold" htmlFor="isActiveCheck">Active (Ava can use this)</label>
                  </div>
                </div>
                <div className="modal-footer bg-light">
                  <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => setShowModal(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary btn-sm">{editingFaq ? 'Update FAQ' : 'Save FAQ'}</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  )
}