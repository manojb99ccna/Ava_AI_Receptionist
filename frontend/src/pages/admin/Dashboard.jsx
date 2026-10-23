import { getAdmin } from '../../services/auth.js'

export default function Dashboard() {
  const admin = getAdmin()

  return (
    <>
      <h3 className="mb-4">Dashboard</h3>
      <div className="card border-0 shadow-sm">
        <div className="card-body">
          


          
        </div>
      </div>
    </>
  )
}
