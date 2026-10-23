import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { clearSession, getAdmin } from "../services/auth.js";

export default function AdminLayout() {
  const navigate = useNavigate();
  const admin = getAdmin();

  function logout() {
    clearSession();
    navigate("/admin/login");
  }

  return (
    <div className="d-flex flex-column min-vh-100 bg-light">
      <nav className="navbar navbar-dark bg-dark px-3">
        <span className="navbar-brand fw-bold">
          <i className="bi bi-headset me-2"></i>Ava AI Admin
        </span>
        <div className="d-flex align-items-center gap-3">
          <span className="text-white-50 small">
            <i className="bi bi-person-circle me-1"></i>
            {admin?.name || admin?.username}
          </span>
          <button className="btn btn-outline-light btn-sm" onClick={logout}>
            <i className="bi bi-box-arrow-right me-1"></i>Logout
          </button>
        </div>
      </nav>
      <div className="d-flex flex-grow-1">
        <aside
          className="bg-white border-end p-3 shadow-sm"
          style={{ width: 240 }}
        >
          <ul className="nav nav-pills flex-column gap-1">
            <li className="nav-item">
              <NavLink
                to="/admin"
                end
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : "text-dark"}`
                }
              >
                <i className="bi bi-speedometer2 me-2"></i>Dashboard
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink
                to="/admin/leads"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : "text-dark"}`
                }
              >
                <i className="bi bi-people me-2"></i>Leads
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink
                to="/admin/conversations"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : "text-dark"}`
                }
              >
                <i className="bi bi-chat-dots me-2"></i>Conversations
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink
                to="/admin/faqs"
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : "text-dark"}`
                }
              >
                <i className="bi bi-question-circle me-2"></i>Business FAQs
              </NavLink>
            </li>
          </ul>
        </aside>

        <main className="flex-grow-1 p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
