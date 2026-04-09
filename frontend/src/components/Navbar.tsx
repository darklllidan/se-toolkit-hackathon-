import { Link, useNavigate } from "react-router-dom";
import { useAuthStore, useThemeStore } from "../store";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <nav style={nav}>
      <Link to="/" style={brand}>
        <span style={{ fontSize: 20 }}>🏛️</span>
        <span>Campus Resource Sync</span>
      </Link>

      <div style={{ flex: 1 }} />

      {user ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Link to="/" style={navLink}>Dashboard</Link>
          <Link to="/profile" style={navLink}>Profile</Link>
          {user.is_admin && (
            <Link to="/admin" style={{ ...navLink, color: "#a78bfa", fontWeight: 600 }}>Admin Panel</Link>
          )}
          <div style={userChip}>
            <span style={userAvatar}>{user.full_name.charAt(0).toUpperCase()}</span>
            <span style={{ fontSize: 13, color: "var(--navbar-text)" }}>
              {user.full_name}
              {user.building ? <span style={{ color: "var(--text-muted)" }}> · D{user.building}/{user.room_number}</span> : null}
            </span>
            {user.is_ta && (
              <span style={{ fontSize: 10, fontWeight: 700, background: "#4f46e5", color: "#fff", borderRadius: 4, padding: "2px 6px", letterSpacing: "0.04em" }}>TA</span>
            )}
          </div>
          <button onClick={handleLogout} style={secondaryBtn}>Sign Out</button>
        </div>
      ) : (
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/login" style={navLink}>Sign In</Link>
          <Link to="/register" style={navBtnLink}>Register</Link>
        </div>
      )}

      <button
        onClick={toggleTheme}
        title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
        style={themeBtn}
        aria-label="Toggle theme"
      >
        {theme === "light" ? "🌙" : "☀️"}
      </button>
    </nav>
  );
}

const nav: React.CSSProperties = {
  height: 56,
  padding: "0 24px",
  background: "var(--bg-navbar)",
  display: "flex",
  alignItems: "center",
  gap: 16,
  borderBottom: "1px solid var(--navbar-border)",
  position: "sticky",
  top: 0,
  zIndex: 500,
  boxShadow: "var(--shadow-sm)",
};

const brand: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  color: "var(--accent-text)",
  fontWeight: 700,
  fontSize: 15,
  textDecoration: "none",
  letterSpacing: "-0.01em",
};

const navLink: React.CSSProperties = {
  color: "var(--navbar-link)",
  textDecoration: "none",
  fontSize: 14,
  padding: "6px 10px",
  borderRadius: 6,
  fontWeight: 500,
};

const navBtnLink: React.CSSProperties = {
  color: "#fff",
  textDecoration: "none",
  fontSize: 14,
  padding: "6px 14px",
  borderRadius: 6,
  fontWeight: 600,
  background: "var(--accent)",
};

const userChip: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: "5px 12px 5px 6px",
};

const userAvatar: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: "50%",
  background: "var(--accent)",
  color: "#fff",
  fontSize: 13,
  fontWeight: 700,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const secondaryBtn: React.CSSProperties = {
  background: "var(--btn-secondary-bg)",
  border: "1px solid var(--border)",
  color: "var(--btn-secondary-text)",
  padding: "6px 14px",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 500,
};

const themeBtn: React.CSSProperties = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  width: 34,
  height: 34,
  cursor: "pointer",
  fontSize: 16,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
  marginLeft: 4,
};
