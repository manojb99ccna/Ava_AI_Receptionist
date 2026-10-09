import { Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout.jsx'
import AdminLayout from '../layouts/AdminLayout.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'
import Home from '../pages/Home.jsx'
import Login from '../pages/admin/Login.jsx'
import Dashboard from '../pages/admin/Dashboard.jsx'
export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
      </Route>

      <Route path="/admin/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<Dashboard />} />        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
