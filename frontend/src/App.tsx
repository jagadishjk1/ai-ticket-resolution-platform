import { Route, Routes, Link, NavLink, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import TicketDetailPage from "./pages/TicketDetailPage";
import "./styles/main.scss";
import "./App.css";

function PageTransition({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransitionStage] = useState("fadeIn");
  useEffect(() => {
    if (location !== displayLocation) {
      setTransitionStage("fadeOut");
    }
  }, [location, displayLocation]);
  return (
    <div
      className={`page-transition ${transitionStage}`}
      onAnimationEnd={() => {
        if (transitionStage === "fadeOut") {
          setTransitionStage("fadeIn");
          setDisplayLocation(location);
        }
      }}
    >
      {children}
    </div>
  );
}

function NotFoundPage() {
  return (
    <div className="history-page">
      <h1>Page not found</h1>
      <Link to="/">← Back to dashboard</Link>
    </div>
  );
}

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <Link to="/" className="app-logo">
            TicketGenie
          </Link>
          <nav className="app-nav" aria-label="Main navigation">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/history">History</NavLink>
          </nav>
        </div>
      </header>
      <main className="app-main">
        <PageTransition>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/ticket/:id" element={<TicketDetailPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </PageTransition>
      </main>
      <footer className="app-footer">
        <p>TicketGenie</p>
        <p>
          &copy; 2026 AI-Powered IT Support Ticket Resolution - MCA Final Year
          Project
        </p>
      </footer>
    </div>
  );
}

export default App;
