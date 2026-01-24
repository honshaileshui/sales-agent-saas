// Layout Component with Sidebar
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Mail, Megaphone, BarChart3, LogOut, Settings } from 'lucide-react';

function Layout({ onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/leads', icon: Users, label: 'Leads' },
    { path: '/emails', icon: Mail, label: 'Emails' },
    { path: '/campaigns', icon: Megaphone, label: 'Campaigns' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  ];

  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <span style={styles.logoIcon}>🚀</span>
          <span style={styles.logoText}>SalesAgent</span>
        </div>

        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {})
              })}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div style={styles.sidebarFooter}>
          <button style={styles.navItem}>
            <Settings size={20} />
            <span>Settings</span>
          </button>
          <button style={styles.logoutBtn} onClick={handleLogout}>
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    background: '#f5f7fa',
  },
  sidebar: {
    width: '260px',
    background: '#1a1a2e',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 0',
    position: 'fixed',
    height: '100vh',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 24px 30px',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    marginBottom: '20px',
  },
  logoIcon: {
    fontSize: '28px',
  },
  logoText: {
    fontSize: '22px',
    fontWeight: '700',
  },
  nav: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    padding: '0 12px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 16px',
    color: 'rgba(255,255,255,0.7)',
    textDecoration: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: '500',
    transition: 'all 0.2s',
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    width: '100%',
    textAlign: 'left',
  },
  navItemActive: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
  },
  sidebarFooter: {
    padding: '0 12px',
    borderTop: '1px solid rgba(255,255,255,0.1)',
    paddingTop: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  logoutBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 16px',
    color: '#ef4444',
    background: 'transparent',
    border: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: '500',
    cursor: 'pointer',
    width: '100%',
    textAlign: 'left',
  },
  main: {
    flex: 1,
    marginLeft: '260px',
    minHeight: '100vh',
  },
};

export default Layout;
