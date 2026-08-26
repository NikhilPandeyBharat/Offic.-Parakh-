import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, Truck, ClipboardCheck, Camera, Factory, Package, 
  AlertTriangle, CheckSquare, RefreshCw, Scale, ShieldAlert, FileText, 
  Settings, LogIn, LogOut, Play, Check, X, Eye, Edit2, Download, AlertCircle, Info
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

interface User {
  username: string;
  role: string;
  full_name: string;
}

export default function App() {
  // Auth state
  const [token, setToken] = useState<string | null>(localStorage.getItem('parakh_token'));
  const [user, setUser] = useState<User | null>(
    localStorage.getItem('parakh_user') ? JSON.parse(localStorage.getItem('parakh_user')!) : null
  );
  
  // Navigation state
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [activeShipmentId, setActiveShipmentId] = useState<number | null>(null);
  const [activeSampleId, setActiveSampleId] = useState<number | null>(null);
  const [activeInspectionId, setActiveInspectionId] = useState<number | null>(null);
  const [activeManufacturerId, setActiveManufacturerId] = useState<number | null>(null);
  const [activeProductId, setActiveProductId] = useState<number | null>(null);

  // Form states
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [loginError, setLoginError] = useState('');

  // Loaded database states
  const [stats, setStats] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [categoryAnalytics, setCategoryAnalytics] = useState<any[]>([]);
  const [geoAnalytics, setGeoAnalytics] = useState<any[]>([]);
  const [shipments, setShipments] = useState<any[]>([]);
  const [activeShipment, setActiveShipment] = useState<any>(null);
  const [manufacturers, setManufacturers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [correctiveActions, setCorrectiveActions] = useState<any[]>([]);
  const [reinspections, setReinspections] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  
  // Inspection workflow states
  const [currentInspection, setCurrentInspection] = useState<any>(null);
  const [cameraFeeds, setCameraFeeds] = useState<any[]>([]);
  const [ocrFacts, setOcrFacts] = useState<any[]>([]);
  const [complianceMatrix, setComplianceMatrix] = useState<any[]>([]);
  const [highlightedFact, setHighlightedFact] = useState<any>(null);
  const [editFieldName, setEditFieldName] = useState<string | null>(null);
  const [editValueInput, setEditValueInput] = useState('');

  // Demo state
  const [demoProgress, setDemoProgress] = useState<{ step: number; text: string } | null>(null);

  // Fetch initial base stats
  useEffect(() => {
    if (token) {
      fetchDashboardData();
      fetchSecondaryData();
    }
  }, [token, currentPage]);

  const fetchDashboardData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      const [resStats, resTrends, resCat, resGeo] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/stats`, { headers }),
        fetch(`${API_BASE}/api/dashboard/trends`, { headers }),
        fetch(`${API_BASE}/api/dashboard/category-analytics`, { headers }),
        fetch(`${API_BASE}/api/dashboard/geography-analytics`, { headers })
      ]);
      if (resStats.ok) setStats(await resStats.json());
      if (resTrends.ok) setTrends(await resTrends.json());
      if (resCat.ok) setCategoryAnalytics(await resCat.json());
      if (resGeo.ok) setGeoAnalytics(await resGeo.json());
    } catch (e) {
      console.error("Error loading dashboard data", e);
    }
  };

  const fetchSecondaryData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      const [resShip, resMfg, resProd, resActions, resRe, resRules, resLogs, resCases] = await Promise.all([
        fetch(`${API_BASE}/api/shipments`, { headers }),
        fetch(`${API_BASE}/api/manufacturers`, { headers }),
        fetch(`${API_BASE}/api/products`, { headers }),
        fetch(`${API_BASE}/api/corrective-actions`, { headers }),
        fetch(`${API_BASE}/api/reinspections`, { headers }),
        fetch(`${API_BASE}/api/rules`, { headers }),
        fetch(`${API_BASE}/api/audit-logs`, { headers }),
        fetch(`${API_BASE}/api/cases`, { headers })
      ]);
      if (resShip.ok) setShipments(await resShip.json());
      if (resMfg.ok) setManufacturers(await resMfg.json());
      if (resProd.ok) setProducts(await resProd.json());
      if (resActions.ok) setCorrectiveActions(await resActions.json());
      if (resRe.ok) setReinspections(await resRe.json());
      if (resRules.ok) setRules(await resRules.json());
      if (resLogs.ok) setAuditLogs(await resLogs.json());
      if (resCases.ok) setCases(await resCases.json());
    } catch (e) {
      console.error("Error loading registry databases", e);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        const userData = { username: data.username, role: data.role, full_name: data.full_name };
        setUser(userData);
        localStorage.setItem('parakh_token', data.access_token);
        localStorage.setItem('parakh_user', JSON.stringify(userData));
        setCurrentPage('dashboard');
      } else {
        const err = await res.json();
        setLoginError(err.detail || 'Login failed');
      }
    } catch (err) {
      setLoginError('Could not reach backend API server');
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('parakh_token');
    localStorage.removeItem('parakh_user');
  };

  // shipment details
  const viewShipment = async (id: number) => {
    setActiveShipmentId(id);
    setCurrentPage('shipment-details');
    try {
      const res = await fetch(`${API_BASE}/api/shipments/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setActiveShipment(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Run lot prioritization
  const prioritizeShipment = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/shipments/${id}/prioritize`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        viewShipment(id);
        fetchSecondaryData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Start E2E Demo sequence
  const startDemoSequence = async () => {
    setDemoProgress({ step: 1, text: "PARAKH loading latest shipment arrival lot..." });
    try {
      // Create a series of timeouts to visually showcase the inspection pipeline steps on front-end
      setTimeout(() => setDemoProgress({ step: 2, text: "Analyzing manufacturer violation rates..." }), 800);
      setTimeout(() => setDemoProgress({ step: 3, text: "Applying explainable risk scoring factors..." }), 1600);
      setTimeout(() => setDemoProgress({ step: 4, text: "Identifying high-priority sample for capture..." }), 2400);
      setTimeout(() => setDemoProgress({ step: 5, text: "Sample selected. Entering multi-camera array..." }), 3200);

      // Trigger E2E backend sequence
      const res = await fetch(`${API_BASE}/api/demo/start-sequence`, {
        method: 'POST'
      });
      
      if (res.ok) {
        const data = await res.json();
        setTimeout(() => setDemoProgress({ step: 6, text: "Synchronized capture triggered. Front/Back/Left/Right/Top views saved." }), 4000);
        setTimeout(() => setDemoProgress({ step: 7, text: "Camera image quality check: Good. Scanner alignment matches packaging size." }), 4800);
        setTimeout(() => setDemoProgress({ step: 8, text: `Packaging identified: ${data.product_name}. Checking registry.` }), 5600);
        setTimeout(() => setDemoProgress({ step: 9, text: "Running OCR word segmentations. Fusing text frames..." }), 6400);
        setTimeout(() => setDemoProgress({ step: 10, text: "Statutory metrology facts normalized. Comparing observed vs rules." }), 7200);
        setTimeout(() => setDemoProgress({ step: 11, text: `Evaluation complete. Verdict: ${data.compliance}. Redirecting...` }), 8000);
        
        setTimeout(() => {
          setDemoProgress(null);
          viewInspection(data.inspection_id);
        }, 8800);
      } else {
        setDemoProgress({ step: -1, text: "Auto sequence failure. Make sure seed data exists." });
        setTimeout(() => setDemoProgress(null), 3000);
      }
    } catch (e) {
      setDemoProgress({ step: -1, text: "Network error occurred." });
      setTimeout(() => setDemoProgress(null), 3000);
    }
  };

  // View inspection profile
  const viewInspection = async (id: number) => {
    setActiveInspectionId(id);
    setCurrentPage('inspection-result');
    try {
      const res = await fetch(`${API_BASE}/api/inspections/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentInspection(data);
        setCameraFeeds(data.captured_images);
        setOcrFacts(data.extracted_facts);
        setComplianceMatrix(data.compliance_evaluations);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Start a fresh manual inspection workflow
  const initiateManualInspection = async (sampleId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/inspections/start?sample_id=${sampleId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setActiveInspectionId(data.id);
        setCurrentPage('capture-station');
        setCurrentInspection(data);
        setCameraFeeds([]);
        setOcrFacts([]);
        setComplianceMatrix([]);
        setHighlightedFact(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Trigger camera capture simulator
  const captureProduct = async () => {
    if (!activeInspectionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/capture`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const feeds = await res.json();
        setCameraFeeds(feeds);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Recapture specific angle
  const recaptureAngle = async (view: string) => {
    if (!activeInspectionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/recapture?camera_view=${view}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        // reload feeds
        const resFeeds = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resFeeds.ok) {
          const data = await resFeeds.json();
          setCameraFeeds(data.captured_images);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Run product identification, OCR, facts extraction
  const processCapturedProduct = async () => {
    if (!activeInspectionId) return;
    try {
      // 1. Identify Product
      await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/identify`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      // 2. OCR Facts
      const resOcr = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/ocr`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resOcr.ok) {
        setOcrFacts(await resOcr.json());
      }
      // 3. Evaluate compliance
      const resEval = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/evaluate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resEval.ok) {
        const evaluation = await resEval.json();
        setComplianceMatrix(evaluation.rules_matrix);
        // Load inspection again
        viewInspection(activeInspectionId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Correct OCR value manually
  const submitFactCorrection = async (fieldName: string) => {
    if (!activeInspectionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/edit-fact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ field_name: fieldName, edited_value: editValueInput })
      });
      if (res.ok) {
        setOcrFacts(await res.json());
        setEditFieldName(null);
        // Refresh compliance evaluations
        const resEval = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resEval.ok) {
          const data = await resEval.json();
          setCurrentInspection(data);
          setComplianceMatrix(data.compliance_evaluations);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Submit Final Verification Decision
  const submitFinalVerdict = async (decision: string, notes: string) => {
    if (!activeInspectionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/inspections/${activeInspectionId}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ final_decision: decision, notes })
      });
      if (res.ok) {
        setCurrentPage('dashboard');
        fetchDashboardData();
        fetchSecondaryData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Schedule a reinspection target
  const triggerReinspectionSchedule = async (actionId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/reinspections/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ corrective_action_id: actionId })
      });
      if (res.ok) {
        fetchSecondaryData();
        setCurrentPage('reinspections');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getProductTimeline = async (id: number) => {
    setActiveProductId(id);
    setCurrentPage('product-details');
  };

  const getManufacturerProfile = async (id: number) => {
    setActiveManufacturerId(id);
    setCurrentPage('manufacturer-details');
  };

  if (!token) {
    return (
      <div className="login-container">
        <form className="login-card" onSubmit={handleLogin}>
          <div style={{ textAlign: 'center', marginBottom: '25px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-info)' }}>PARAKH</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '5px' }}>
              Legal Metrology Intelligence Command Portal
            </p>
          </div>
          {loginError && (
            <div style={{
              backgroundColor: 'var(--color-danger-bg)',
              color: 'var(--color-danger)',
              padding: '10px',
              borderRadius: '6px',
              fontSize: '13px',
              marginBottom: '15px'
            }}>
              {loginError}
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Username</label>
            <input 
              type="text" 
              className="form-control" 
              value={usernameInput} 
              onChange={e => setUsernameInput(e.target.value)} 
              required 
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-control" 
              value={passwordInput} 
              onChange={e => setPasswordInput(e.target.value)} 
              required 
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '10px' }}>
            <LogIn size={16} /> Authenticate
          </button>
          
          <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '15px', fontSize: '11px', color: 'var(--text-dim)' }}>
            <strong>Demo Accounts Available:</strong>
            <ul style={{ listStyle: 'none', marginTop: '5px' }}>
              <li>• Operator: <code>operator</code> / <code>operator123</code></li>
              <li>• Verification: <code>verification</code> / <code>verification123</code></li>
              <li>• Director: <code>enforcement</code> / <code>enforcement123</code></li>
              <li>• Admin: <code>admin</code> / <code>admin123</code></li>
            </ul>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo-icon">P</div>
          <div>
            <div className="logo-text">PARAKH</div>
            <div className="logo-tag">SIH Prototype</div>
          </div>
        </div>
        
        <ul className="sidebar-menu">
          <li className={`menu-item ${currentPage === 'dashboard' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('dashboard')}>
              <LayoutDashboard size={18} /> Overview
            </button>
          </li>
          
          <li className={`menu-item ${currentPage === 'shipments' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('shipments')}>
              <Truck size={18} /> Shipments Inspection
            </button>
          </li>
          
          <li className={`menu-item ${currentPage === 'manufacturers' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('manufacturers')}>
              <Factory size={18} /> Manufacturers Registry
            </button>
          </li>

          <li className={`menu-item ${currentPage === 'products' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('products')}>
              <Package size={18} /> Product Timelines
            </button>
          </li>

          <li className={`menu-item ${currentPage === 'corrective-actions' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('corrective-actions')}>
              <CheckSquare size={18} /> Corrective Notices
            </button>
          </li>

          <li className={`menu-item ${currentPage === 'reinspections' ? 'active' : ''}`}>
            <button onClick={() => setCurrentPage('reinspections')}>
              <RefreshCw size={18} /> Re-Inspections
            </button>
          </li>

          {user?.role === 'ADMIN' && (
            <>
              <div style={{ padding: '15px 15px 5px', fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: '0.5px' }}>Admin Controls</div>
              <li className={`menu-item ${currentPage === 'rules-mgmt' ? 'active' : ''}`}>
                <button onClick={() => setCurrentPage('rules-mgmt')}>
                  <Scale size={18} /> Rule Management
                </button>
              </li>
              <li className={`menu-item ${currentPage === 'audit-logs' ? 'active' : ''}`}>
                <button onClick={() => setCurrentPage('audit-logs')}>
                  <Settings size={18} /> System Audit Logs
                </button>
              </li>
            </>
          )}
        </ul>

        <div className="sidebar-footer">
          <div className="user-info">
            <div>{user?.full_name}</div>
            <div className="user-role">{user?.role}</div>
          </div>
          <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', width: '100%' }} onClick={handleLogout}>
            <LogOut size={14} /> Log Out
          </button>
        </div>
      </div>

      {/* Main Content Pane */}
      <div className="main-content">
        <div className="header">
          <div className="header-title">
            {currentPage === 'dashboard' && "Enforcement Intelligence Dashboard"}
            {currentPage === 'shipments' && "Shipment Shipments Directory"}
            {currentPage === 'shipment-details' && `Shipment Lots Summary: ${activeShipment?.shipment_number || ''}`}
            {currentPage === 'capture-station' && "Simulated Multi-Camera Inspection Station"}
            {currentPage === 'inspection-result' && "Inspection Statutory Compliance Analysis"}
            {currentPage === 'manufacturers' && "Manufacturer Enforcement Risk Profile"}
            {currentPage === 'manufacturer-details' && "Manufacturer Compliance Analytics"}
            {currentPage === 'products' && "Product Label Timeline Registry"}
            {currentPage === 'product-details' && "Product Label Timeline"}
            {currentPage === 'corrective-actions' && "Statutory Corrective Actions"}
            {currentPage === 'reinspections' && "Scheduled Packaging Re-Inspections"}
            {currentPage === 'rules-mgmt' && "Legal Metrology Rules Configurations"}
            {currentPage === 'audit-logs' && "System Administrative Audit Trail"}
          </div>
          
          <div className="header-actions">
            <button className="btn btn-secondary" style={{ fontSize: '12px' }} onClick={fetchSecondaryData}>
              <RefreshCw size={14} /> Refresh Data
            </button>
          </div>
        </div>

        <div className="content-body">
          {/* 1. DASHBOARD OVERVIEW */}
          {currentPage === 'dashboard' && stats && (
            <div>
              {/* Cards Metrics */}
              <div className="grid-4">
                <div className="metric-card">
                  <div className="metric-icon" style={{ backgroundColor: 'var(--color-info-bg)', color: 'var(--color-info)' }}>
                    <Truck size={20} />
                  </div>
                  <div className="metric-info">
                    <span className="metric-label">Inspected Shipments</span>
                    <span className="metric-value">{stats.inspected_shipments_count} / {stats.shipments_count}</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon" style={{ backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success)' }}>
                    <ClipboardCheck size={20} />
                  </div>
                  <div className="metric-info">
                    <span className="metric-label">Compliance Rate</span>
                    <span className="metric-value">{stats.compliance_rate}%</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon" style={{ backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)' }}>
                    <ShieldAlert size={20} />
                  </div>
                  <div className="metric-info">
                    <span className="metric-label">High-Risk Manufact.</span>
                    <span className="metric-value">{stats.high_risk_manufacturers_count} / {stats.manufacturers_count}</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon" style={{ backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
                    <CheckSquare size={20} />
                  </div>
                  <div className="metric-info">
                    <span className="metric-label">Open Notices</span>
                    <span className="metric-value">{stats.open_corrective_actions_count}</span>
                  </div>
                </div>
              </div>

              <div className="grid-2">
                {/* SVG Line Chart Trend */}
                <div className="card">
                  <div className="card-title">Compliance & Violations Trends</div>
                  <div style={{ height: '220px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', padding: '10px 20px' }}>
                    {trends.map((item, idx) => (
                      <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '5px' }}>{item.compliance_rate}%</div>
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '140px', width: '100%', justifyContent: 'center' }}>
                          {/* Compliance Bar */}
                          <div style={{ 
                            height: `${item.inspections * 4}px`, 
                            width: '16px', 
                            backgroundColor: 'var(--color-info)',
                            borderRadius: '2px 2px 0 0'
                          }} title={`Inspections: ${item.inspections}`} />
                          {/* Violations Bar */}
                          <div style={{ 
                            height: `${item.violations * 4}px`, 
                            width: '16px', 
                            backgroundColor: 'var(--color-danger)',
                            borderRadius: '2px 2px 0 0'
                          }} title={`Violations: ${item.violations}`} />
                        </div>
                        <div style={{ fontSize: '10px', marginTop: '8px', color: 'var(--text-dim)' }}>{item.period}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', fontSize: '11px', marginTop: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--color-info)', display: 'inline-block' }} /> Inspected Samples
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ width: '10px', height: '10px', backgroundColor: 'var(--color-danger)', display: 'inline-block' }} /> Detected Violations
                    </div>
                  </div>
                </div>

                {/* Categories Breakdown */}
                <div className="card">
                  <div className="card-title">Metrology Violations by Product Category</div>
                  <div className="table-container">
                    <table className="dense-table">
                      <thead>
                        <tr>
                          <th>Category</th>
                          <th>Inspected</th>
                          <th>Violations</th>
                          <th>Compliance Rate</th>
                          <th>Risk Tier</th>
                        </tr>
                      </thead>
                      <tbody>
                        {categoryAnalytics.map((item, idx) => (
                          <tr key={idx}>
                            <td>{item.category}</td>
                            <td>{item.inspections}</td>
                            <td>{item.violations}</td>
                            <td>{item.compliance_rate}%</td>
                            <td>
                              <span className={`badge badge-${item.risk.toLowerCase()}`}>{item.risk}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Geographic Analytics Map representation */}
              <div className="card">
                <div className="card-title">Regional Metrology Violation Densities</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ fontSize: '14px', marginBottom: '10px', color: 'var(--text-muted)' }}>Top Offenders by State</h4>
                    {geoAnalytics.map((item, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)', fontSize: '13px' }}>
                        <span>{item.state}</span>
                        <span style={{ fontWeight: 600, color: 'var(--color-danger)' }}>{item.violations} Violations</span>
                      </div>
                    ))}
                  </div>
                  
                  {/* Mock Graphical Map Layout */}
                  <div style={{
                    height: '240px',
                    border: '1px solid var(--border-color)',
                    backgroundColor: 'rgba(0,0,0,0.2)',
                    borderRadius: '8px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative'
                  }}>
                    <span style={{ color: 'var(--text-dim)', fontSize: '12px' }}>[ Simulated Geographic Enforcement Heatmap ]</span>
                    {/* Mock region circles */}
                    <div style={{ position: 'absolute', top: '40px', left: '120px', width: '30px', height: '30px', borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.4)', border: '2px solid var(--color-danger)' }} title="Haryana Zone: High Density" />
                    <div style={{ position: 'absolute', top: '110px', left: '160px', width: '20px', height: '20px', borderRadius: '50%', backgroundColor: 'rgba(245, 158, 11, 0.4)', border: '2px solid var(--color-warning)' }} title="Gujarat Zone" />
                    <div style={{ position: 'absolute', top: '160px', left: '260px', width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.5)', border: '2px solid var(--color-danger)' }} title="Maharashtra Zone: Critical" />
                    <div style={{ position: 'absolute', top: '180px', left: '320px', width: '15px', height: '15px', borderRadius: '50%', backgroundColor: 'rgba(16, 185, 129, 0.4)', border: '2px solid var(--color-success)' }} title="Tamil Nadu Zone" />
                  </div>
                </div>
              </div>

              {/* Active Enforcement Priority Recommendations */}
              <div className="card">
                <div className="card-title">Enforcement priorities: System recommendations</div>
                <div className="table-container">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Manufacturer</th>
                        <th>State</th>
                        <th>Risk Rating</th>
                        <th>Compliance Score</th>
                        <th>Recommended Action</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {manufacturers.slice(0, 5).map((mfg, idx) => (
                        <tr key={idx}>
                          <td><strong>{mfg.name}</strong></td>
                          <td>{mfg.state}</td>
                          <td>
                            <span style={{ fontWeight: 700 }} className={`risk-${mfg.risk_score >= 80 ? 'CRITICAL' : mfg.risk_score >= 60 ? 'HIGH' : mfg.risk_score >= 40 ? 'MEDIUM' : 'LOW'}`}>
                              {mfg.risk_score.toFixed(1)} / 100
                            </span>
                          </td>
                          <td>{mfg.compliance_rate.toFixed(1)}%</td>
                          <td>
                            <span className={`badge badge-${mfg.risk_score >= 80 ? 'non_compliant' : mfg.risk_score >= 60 ? 'requires_verification' : 'compliant'}`}>
                              {mfg.risk_score >= 80 ? 'PROSECUTE / AUDIT' : mfg.risk_score >= 60 ? 'PRIORITY SAMPLING' : 'ROUTINE MONITORING'}
                            </span>
                          </td>
                          <td>
                            <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px' }} onClick={() => getManufacturerProfile(mfg.id)}>
                              <Eye size={12} /> Inspect
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* 2. SHIPMENTS LIST */}
          {currentPage === 'shipments' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Shipment ID</th>
                      <th>Date Received</th>
                      <th>Lot Count</th>
                      <th>Total Items</th>
                      <th>Inspection Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shipments.map((shp, idx) => (
                      <tr key={idx}>
                        <td><strong>{shp.shipment_number}</strong></td>
                        <td>{new Date(shp.date_received).toLocaleDateString()}</td>
                        <td>{shp.lot_count} Lots</td>
                        <td>{shp.item_count.toLocaleString()} units</td>
                        <td>
                          <span className={`badge badge-${shp.status.toLowerCase()}`}>{shp.status}</span>
                        </td>
                        <td>
                          <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => viewShipment(shp.id)}>
                            Review Lots
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. SHIPMENT DETAILS */}
          {currentPage === 'shipment-details' && activeShipment && (
            <div>
              <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '16px' }}>Summary: {activeShipment.shipment_number}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                    Contains {activeShipment.lot_count} lots, totaling {activeShipment.item_count.toLocaleString()} retail items.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button className="btn btn-secondary" onClick={() => setCurrentPage('shipments')}>Back to List</button>
                  <button className="btn btn-primary" onClick={() => prioritizeShipment(activeShipment.id)}>
                    <Play size={14} /> Prioritize Sampling
                  </button>
                </div>
              </div>

              <div className="card">
                <div className="card-title">Risk-Based Sample Prioritization Matrix</div>
                <div className="table-container">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Product / Brand</th>
                        <th>Manufacturer</th>
                        <th>Category</th>
                        <th>Lot Quantity</th>
                        <th>Prioritized Risk Score</th>
                        <th>Sampling Target Status</th>
                        <th>Action Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeShipment.lots.map((lot: any, idx: number) => {
                        const score = lot.risk_score;
                        const statusClass = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW';
                        return (
                          <tr key={idx}>
                            <td><strong>{lot.product.name}</strong><br/><span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>UPC: {lot.product.barcode}</span></td>
                            <td>{lot.product.manufacturer.name}</td>
                            <td>{lot.product.category.name}</td>
                            <td>{lot.quantity.toLocaleString()} units</td>
                            <td>
                              <span style={{ fontWeight: 700 }} className={`risk-${statusClass}`}>
                                {score.toFixed(1)} / 100
                              </span>
                            </td>
                            <td>
                              <span className={`badge badge-${lot.priority_status.toLowerCase()}`}>
                                {lot.priority_status === 'CRITICAL' || lot.priority_status === 'HIGH' ? 'PRIORITY SAMPLE' : 'ROUTINE TARGET'}
                              </span>
                            </td>
                            <td>
                              <button 
                                className="btn btn-primary" 
                                style={{ padding: '6px 12px', fontSize: '12px' }} 
                                onClick={async () => {
                                  // Find a pending sample inside this lot
                                  const res = await fetch(`${API_BASE}/api/samples?lot_id=${lot.id}`, {
                                    headers: { 'Authorization': `Bearer ${token}` }
                                  });
                                  if (res.ok) {
                                    const samples = await res.json();
                                    const pending = samples.find((s: any) => s.status === 'PENDING');
                                    if (pending) {
                                      initiateManualInspection(pending.id);
                                    } else {
                                      alert("All samples in this lot have been processed!");
                                    }
                                  }
                                }}
                              >
                                Capture Station
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* 4. MULTI-CAMERA CAPTURE STATION */}
          {currentPage === 'capture-station' && currentInspection && (
            <div>
              <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '16px' }}>Inspection ID: INSP-{currentInspection.id.toString().padStart(6, '0')}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                    Target: <strong>{currentInspection.sample?.lot?.product?.name}</strong> | Serial: <code>{currentInspection.sample?.serial_number}</code>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button className="btn btn-secondary" onClick={() => viewShipment(currentInspection.sample.lot.shipment_id)}>
                    Cancel
                  </button>
                  <button className="btn btn-primary" onClick={captureProduct}>
                    <Camera size={14} /> Capture 5 Views
                  </button>
                  {cameraFeeds.length > 0 && (
                    <button className="btn btn-success" onClick={processCapturedProduct} disabled={cameraFeeds.some(f => f.quality_status !== 'GOOD')}>
                      Start OCR Evaluation
                    </button>
                  )}
                </div>
              </div>

              {/* 5-camera feed layout */}
              <div className="camera-grid">
                {["FRONT", "BACK", "LEFT", "RIGHT", "TOP"].map((view, idx) => {
                  const feed = cameraFeeds.find(f => f.camera_view === view);
                  const isGlare = feed?.quality_status === 'GLARE';
                  const isBlur = feed?.quality_status === 'BLUR';
                  
                  // Product packaging dynamic layout mock representation
                  const p_barcode = currentInspection.sample?.lot?.product?.barcode;
                  let styleClass = "generic";
                  if (p_barcode === "8901000000001") styleClass = "biscuit";
                  if (p_barcode === "8901000000003") styleClass = "cream";
                  if (p_barcode === "8901000000007") styleClass = "beer";

                  return (
                    <div className={`camera-feed ${feed ? 'active' : ''}`} key={idx}>
                      <span className="camera-feed-label">CAM-{idx+1} // {view}</span>
                      {feed ? (
                        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
                          {/* Image Sim drawing */}
                          <div className={`simulated-packaging ${styleClass}`} style={{ filter: isBlur ? 'blur(5px)' : 'none' }}>
                            <div style={{ fontSize: '12px', fontWeight: 700 }}>{currentInspection.sample?.lot?.product?.name.split(' ')[0]}</div>
                            <div style={{ fontSize: '9px', opacity: 0.6 }}>[ {view} VIEW IMAGE ]</div>
                            {isGlare && (
                              <div style={{
                                position: 'absolute',
                                width: '80px',
                                height: '80px',
                                background: 'radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%)',
                                top: '25%',
                                left: '35%'
                              }} />
                            )}
                          </div>
                          
                          {/* Status Badge */}
                          <span className={`camera-feed-status badge badge-${feed.quality_status.toLowerCase()}`}>
                            {feed.quality_status}
                          </span>

                          {/* Recapture button on fail */}
                          {(isGlare || isBlur) && (
                            <div style={{
                              position: 'absolute',
                              inset: 0,
                              backgroundColor: 'rgba(0,0,0,0.6)',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '10px'
                            }}>
                              <AlertTriangle size={24} color="var(--color-danger)" />
                              <span style={{ fontSize: '11px', color: '#fff' }}>Image quality check failed</span>
                              <button className="btn btn-primary" style={{ padding: '4px 10px', fontSize: '10px' }} onClick={() => recaptureAngle(view)}>
                                Recapture View
                              </button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="camera-viewfinder">
                          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>FEED OFFLINE</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 5. INSPECTION RESULT & COMPLIANCE MATRIX */}
          {currentPage === 'inspection-result' && currentInspection && (
            <div>
              {/* Top Summary Info Card */}
              <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '16px' }}>Inspection ID: INSP-{currentInspection.id.toString().padStart(6, '0')}</h3>
                  <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginTop: '6px' }}>
                    <span className={`badge badge-${currentInspection.overall_compliance.toLowerCase()}`}>
                      Verdict: {currentInspection.overall_compliance.replace("_", " ")}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      Coverage: <strong>{currentInspection.overall_coverage}%</strong>
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      Target: {currentInspection.sample.lot.product.name}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <a className="btn btn-secondary" href={`${API_BASE}/api/inspections/${currentInspection.id}/pdf`} target="_blank" rel="noreferrer">
                    <Download size={14} /> Download PDF Report
                  </a>
                  {user?.role === 'VERIFICATION_OFFICER' && currentInspection.status === 'IN_PROGRESS' && (
                    <>
                      <button className="btn btn-danger" onClick={() => submitFinalVerdict('FAIL', "Mandatory statutory declarations (mrp / consumer helpline contact) are missing or layout is unreadable.")}>
                        Reject (FAIL)
                      </button>
                      <button className="btn btn-success" onClick={() => submitFinalVerdict('PASS', "Statutory packaging declarations comply with Metrology standards.")}>
                        Verify & Approve (PASS)
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="grid-2">
                {/* A: Extracted Metrology Facts (Observed facts) */}
                <div className="card">
                  <div className="card-title">Extracted Statutory Declarations (A)</div>
                  <div className="table-container">
                    <table className="dense-table">
                      <thead>
                        <tr>
                          <th>Declaration Field</th>
                          <th>OCR Extracted Label</th>
                          <th>Confidence</th>
                          <th>Verification</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ocrFacts.map((fact, idx) => (
                          <tr 
                            key={idx} 
                            style={{ 
                              cursor: 'pointer',
                              backgroundColor: highlightedFact?.id === fact.id ? 'rgba(59,130,246,0.06)' : 'transparent'
                            }}
                            onClick={() => setHighlightedFact(fact)}
                          >
                            <td><strong>{fact.field_name.replace("_", " ").toUpperCase()}</strong></td>
                            <td>
                              {editFieldName === fact.field_name ? (
                                <div style={{ display: 'flex', gap: '5px' }}>
                                  <input 
                                    type="text" 
                                    className="form-control" 
                                    style={{ padding: '2px 6px', fontSize: '12px' }} 
                                    value={editValueInput} 
                                    onChange={e => setEditValueInput(e.target.value)} 
                                  />
                                  <button className="btn btn-success" style={{ padding: '2px 6px' }} onClick={() => submitFactCorrection(fact.field_name)}>
                                    <Check size={10} />
                                  </button>
                                  <button className="btn btn-danger" style={{ padding: '2px 6px' }} onClick={() => setEditFieldName(null)}>
                                    <X size={10} />
                                  </button>
                                </div>
                              ) : (
                                <span>{fact.extracted_value}</span>
                              )}
                            </td>
                            <td>
                              <span style={{ 
                                fontWeight: 600, 
                                color: fact.confidence > 85 ? 'var(--color-success)' : fact.confidence > 60 ? 'var(--color-warning)' : 'var(--color-danger)'
                              }}>
                                {fact.confidence.toFixed(1)}%
                              </span>
                            </td>
                            <td>
                              {user?.role === 'VERIFICATION_OFFICER' && editFieldName !== fact.field_name && (
                                <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: '10px' }} onClick={(e) => {
                                  e.stopPropagation();
                                  setEditFieldName(fact.field_name);
                                  setEditValueInput(fact.extracted_value);
                                }}>
                                  <Edit2 size={10} /> Edit
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* B: Compliance checklist matrix */}
                <div className="card">
                  <div className="card-title">Statutory Requirements Checklist Matrix (B)</div>
                  <div className="table-container">
                    <table className="dense-table">
                      <thead>
                        <tr>
                          <th>Rule Reference</th>
                          <th>Provision / Regulation</th>
                          <th>Result status</th>
                          <th>Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {complianceMatrix.map((item, idx) => {
                          const code = item.rule_version?.rule?.rule_code || `RULE-DEMO-00${idx+1}`;
                          const title = item.rule_version?.rule?.title || "Declaration Rule";
                          return (
                            <tr key={idx}>
                              <td><code style={{ color: 'var(--color-info)' }}>{code}</code></td>
                              <td>{title}</td>
                              <td>
                                <span className={`badge badge-${item.status.toLowerCase()}`}>
                                  {item.status.replace("_", " ")}
                                </span>
                              </td>
                              <td style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.notes}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Evidence Crop Panel */}
              {highlightedFact && (
                <div className="card">
                  <div className="card-title">Cropped Evidence Region Frame</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
                    <div className="evidence-crop-container">
                      {/* Drawing mock crop representation of packaging labels */}
                      <div className="simulated-packaging biscuit" style={{ width: '100%', height: '100%' }}>
                        <div style={{ opacity: 0.2, fontSize: '10px' }}>[ 3D Camera Feed Label Capture View ]</div>
                        <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '20px' }}>
                          {highlightedFact.extracted_value}
                        </div>
                      </div>
                      
                      {/* Highlight Crop Bbox */}
                      <div className="evidence-label-overlay" style={{
                        top: '40%',
                        left: '20%',
                        width: '60%',
                        height: '25%'
                      }} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                      <div><strong>Field Type:</strong> <span style={{ fontFamily: 'var(--font-mono)' }}>{highlightedFact.field_name}</span></div>
                      <div><strong>Raw Text Extracted:</strong> <span style={{ color: 'var(--color-warning)' }}>"{highlightedFact.extracted_value}"</span></div>
                      <div><strong>Normalized Value:</strong> <span style={{ color: 'var(--color-success)' }}>{highlightedFact.normalized_value}</span></div>
                      <div><strong>System confidence:</strong> <strong>{highlightedFact.confidence.toFixed(1)}%</strong></div>
                      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px', fontSize: '11px', color: 'var(--text-dim)' }}>
                        * This crop is saved permanently in the institutional memory (Variable C database) and mapped to audit trail records.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 6. MANUFACTURERS LIST */}
          {currentPage === 'manufacturers' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Manufacturer Code</th>
                      <th>Company Name</th>
                      <th>Location City</th>
                      <th>State Region</th>
                      <th>Institutional Risk Rating</th>
                      <th>Last Inspection Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manufacturers.map((mfg, idx) => {
                      const scoreClass = mfg.risk_score >= 80 ? 'CRITICAL' : mfg.risk_score >= 60 ? 'HIGH' : mfg.risk_score >= 40 ? 'MEDIUM' : 'LOW';
                      return (
                        <tr key={idx}>
                          <td><code>{mfg.code}</code></td>
                          <td><strong>{mfg.name}</strong></td>
                          <td>{mfg.city}</td>
                          <td>{mfg.state}</td>
                          <td>
                            <span style={{ fontWeight: 700 }} className={`risk-${scoreClass}`}>
                              {mfg.risk_score.toFixed(1)} / 100
                            </span>
                          </td>
                          <td>{mfg.last_inspection_date ? new Date(mfg.last_inspection_date).toLocaleDateString() : 'Never'}</td>
                          <td>
                            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => getManufacturerProfile(mfg.id)}>
                              View Profile
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 7. MANUFACTURER DETAILS & HISTORICAL RISK BREAKDOWN */}
          {currentPage === 'manufacturer-details' && activeManufacturerId && (
            <div>
              {/* Load details dynamically if profiles state fetched */}
              {(() => {
                const item = manufacturers.find(m => m.id === activeManufacturerId);
                if (!item) return <div>Loading Profile...</div>;
                
                return (
                  <div>
                    <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h3 style={{ fontSize: '18px' }}>{item.name}</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                          Address: {item.address}, {item.city}, {item.state}
                        </p>
                      </div>
                      <button className="btn btn-secondary" onClick={() => setCurrentPage('manufacturers')}>Back to List</button>
                    </div>

                    <div className="grid-2">
                      {/* Risk factors Breakdown */}
                      <div className="card">
                        <div className="card-title">Institutional Risk Factors Breakdown</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' }}>
                          <div style={{
                            width: '100px',
                            height: '100px',
                            borderRadius: '50%',
                            border: '8px solid var(--border-color)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            borderColor: item.risk_score >= 80 ? 'var(--risk-critical)' : item.risk_score >= 60 ? 'var(--risk-high)' : 'var(--risk-medium)'
                          }}>
                            <span style={{ fontSize: '20px', fontWeight: 700 }}>{item.risk_score.toFixed(0)}</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SCORE</span>
                          </div>
                          <div>
                            <div style={{ fontSize: '14px', fontWeight: 600 }}>Risk Tier: <span className={`risk-${item.risk_score >= 80 ? 'CRITICAL' : item.risk_score >= 60 ? 'HIGH' : 'MEDIUM'}`}>{item.risk_score >= 80 ? 'CRITICAL' : item.risk_score >= 60 ? 'HIGH' : item.risk_score >= 40 ? 'MEDIUM' : 'LOW'}</span></div>
                            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                              This score determines sampling priorities for shipments containing lots from this manufacturer.
                            </p>
                          </div>
                        </div>

                        {/* Factors breakdown */}
                        <div className="factors-list">
                          <div className="factor-item">
                            <span>Category Base Risk Factor</span>
                            <span className="factor-impact" style={{ color: 'var(--color-info)' }}>+15.0</span>
                          </div>
                          <div className="factor-item">
                            <span>Prior Violation Frequency Count</span>
                            <span className="factor-impact" style={{ color: 'var(--color-warning)' }}>+{item.risk_score >= 60 ? '30.0' : '15.0'}</span>
                          </div>
                          <div className="factor-item">
                            <span>Repeat Violations Flag</span>
                            <span className="factor-impact" style={{ color: 'var(--color-danger)' }}>+{item.risk_score >= 70 ? '25.0' : '0.0'}</span>
                          </div>
                          <div className="factor-item">
                            <span>Corrective Action Resolutions</span>
                            <span className="factor-impact" style={{ color: 'var(--color-success)' }}>-5.0</span>
                          </div>
                        </div>
                      </div>

                      {/* Compliance Registry History */}
                      <div className="card">
                        <div className="card-title">Enforcement Analytics History</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                            <span>Total Inspected Lots:</span>
                            <strong>{item.risk_score >= 60 ? '18 lots' : '4 lots'}</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                            <span>Overall Compliance Rate:</span>
                            <strong style={{ color: item.compliance_rate > 90 ? 'var(--color-success)' : 'var(--color-warning)' }}>{item.compliance_rate.toFixed(1)}%</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                            <span>Pending Open Corrective Notices:</span>
                            <strong style={{ color: 'var(--color-danger)' }}>{item.risk_score >= 60 ? '2 notices' : '0'}</strong>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* 8. PRODUCTS LIST */}
          {currentPage === 'products' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Barcode ID</th>
                      <th>Product Brand / Name</th>
                      <th>Manufacturer</th>
                      <th>Category</th>
                      <th>Current Version</th>
                      <th>Status State</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((prod, idx) => (
                      <tr key={idx}>
                        <td><code>{prod.barcode}</code></td>
                        <td><strong>{prod.name}</strong></td>
                        <td>{prod.manufacturer?.name}</td>
                        <td>{prod.category?.name}</td>
                        <td><span className="badge badge-compliant">{prod.current_version}</span></td>
                        <td>
                          <span className={`badge badge-${prod.status.toLowerCase()}`}>{prod.status}</span>
                        </td>
                        <td>
                          <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => getProductTimeline(prod.id)}>
                            View Timeline
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 9. PRODUCT DETAILS & PACKAGING TIMELINE */}
          {currentPage === 'product-details' && activeProductId && (
            <div>
              {(() => {
                const prod = products.find(p => p.id === activeProductId);
                if (!prod) return <div>Loading...</div>;

                return (
                  <div>
                    <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h3 style={{ fontSize: '16px' }}>Product: {prod.name}</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
                          Manufacturer: {prod.manufacturer?.name} | Barcode: <code>{prod.barcode}</code>
                        </p>
                      </div>
                      <button className="btn btn-secondary" onClick={() => setCurrentPage('products')}>Back to List</button>
                    </div>

                    {/* Packaging Version Comparisons */}
                    <div className="card">
                      <div className="card-title">Design Packaging Revisions Comparer</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                        <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '15px', textAlign: 'center' }}>
                          <span className="badge badge-fail" style={{ marginBottom: '10px' }}>Version v1 (FAILED)</span>
                          <div className="simulated-packaging biscuit" style={{ height: '150px' }}>
                            <div style={{ fontSize: '12px' }}>Digestive Biscuits</div>
                            <div style={{ color: 'var(--color-danger)', fontSize: '10px', marginTop: '10px' }}>[ Missing Consumer Helpline ]</div>
                          </div>
                        </div>
                        
                        <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '15px', textAlign: 'center' }}>
                          <span className="badge badge-pass" style={{ marginBottom: '10px' }}>Version v2 (PASSED)</span>
                          <div className="simulated-packaging biscuit" style={{ height: '150px' }}>
                            <div style={{ fontSize: '12px' }}>Digestive Biscuits</div>
                            <div style={{ color: 'var(--color-success)', fontSize: '10px', marginTop: '10px' }}>[ Helpline: 1800-000-0000 Added ]</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* 10. CORRECTIVE ACTIONS */}
          {currentPage === 'corrective-actions' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Notice ID</th>
                      <th>Inspection Source</th>
                      <th>Manufacturer</th>
                      <th>Target Product</th>
                      <th>Date Issued</th>
                      <th>Notice Status</th>
                      <th>Enforcement Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {correctiveActions.map((action, idx) => (
                      <tr key={idx}>
                        <td><code>ACT-{action.id.toString().padStart(5, '0')}</code></td>
                        <td>
                          <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => viewInspection(action.inspection_id)}>
                            INSP-{action.inspection_id.toString().padStart(6, '0')}
                          </button>
                        </td>
                        <td><strong>{action.manufacturer?.name}</strong></td>
                        <td>{action.product?.name}</td>
                        <td>{new Date(action.date_issued).toLocaleDateString()}</td>
                        <td>
                          <span className={`badge badge-${action.status.toLowerCase()}`}>{action.status}</span>
                        </td>
                        <td>
                          {action.status === 'OPEN' && (
                            <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={() => triggerReinspectionSchedule(action.id)}>
                              Schedule Re-Inspection
                            </button>
                          )}
                          {action.status === 'RESOLVED' && <span style={{ fontSize: '12px', color: 'var(--color-success)' }}>Resolved (v2 updated)</span>}
                          {action.status === 'FAILED' && <span style={{ fontSize: '12px', color: 'var(--color-danger)' }}>Prosecution Initiated</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 11. RE-INSPECTIONS */}
          {currentPage === 'reinspections' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Re-Inspection ID</th>
                      <th>Corrective Action Target</th>
                      <th>Original Failure</th>
                      <th>New Inspection Link</th>
                      <th>Process Status</th>
                      <th>Verdict Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reinspections.map((re, idx) => (
                      <tr key={idx}>
                        <td><code>REINSP-{re.id.toString().padStart(5, '0')}</code></td>
                        <td><code>ACT-{re.corrective_action_id.toString().padStart(5, '0')}</code></td>
                        <td>
                          <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => viewInspection(re.original_inspection_id)}>
                            Original INSP
                          </button>
                        </td>
                        <td>
                          {re.new_inspection_id ? (
                            <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => viewInspection(re.new_inspection_id)}>
                              Re-INSP {re.new_inspection_id}
                            </button>
                          ) : (
                            <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Pending execution</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge badge-${re.status.toLowerCase()}`}>{re.status}</span>
                        </td>
                        <td>
                          {re.comparison_result ? (
                            <span className={`badge badge-${re.comparison_result === 'RESOLVED' ? 'compliant' : 'non_compliant'}`}>
                              {re.comparison_result}
                            </span>
                          ) : (
                            <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '11px' }} onClick={() => {
                              // Direct trigger E2E loop
                              startDemoSequence();
                            }}>
                              Run Re-Inspection Capture
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 12. RULES CONFIG (Admin) */}
          {currentPage === 'rules-mgmt' && (
            <div className="card">
              <div className="card-title">Statutory Legal Metrology Rules Registry</div>
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Rule Code</th>
                      <th>Rule Description</th>
                      <th>Severity</th>
                      <th>Version Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.map((rule, idx) => (
                      <tr key={idx}>
                        <td><code style={{ color: 'var(--color-info)' }}>{rule.rule_code}</code></td>
                        <td><strong>{rule.title}</strong><br/><span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{rule.description}</span></td>
                        <td><span className={`badge badge-${rule.severity.toLowerCase()}`}>{rule.severity}</span></td>
                        <td>
                          <span className="badge badge-compliant">Active (v1)</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 13. AUDIT LOGS (Admin) */}
          {currentPage === 'audit-logs' && (
            <div className="card">
              <div className="table-container">
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Time log</th>
                      <th>User Account</th>
                      <th>Action category</th>
                      <th>Activity Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log, idx) => (
                      <tr key={idx}>
                        <td><code style={{ fontSize: '12px' }}>{new Date(log.timestamp).toLocaleString()}</code></td>
                        <td><strong>{log.user?.username || 'System'}</strong></td>
                        <td><span className="badge badge-compliant" style={{ fontFamily: 'var(--font-mono)' }}>{log.action}</span></td>
                        <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{log.details}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Floating START DEMO INSPECTION Button */}
      <div className="demo-trigger-container">
        <button className="demo-trigger-btn" onClick={startDemoSequence}>
          <Play size={16} fill="black" /> START DEMO INSPECTION
        </button>
      </div>

      {/* Full screen E2E progress loader overlay */}
      {demoProgress && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(5, 7, 10, 0.95)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '20px'
        }}>
          {demoProgress.step === -1 ? (
            <AlertCircle size={44} color="var(--color-danger)" />
          ) : (
            <div style={{
              width: '50px',
              height: '50px',
              border: '4px solid var(--border-color)',
              borderTopColor: 'var(--color-warning)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
          )}
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
          
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#fff', letterSpacing: '0.5px' }}>
            {demoProgress.step === -1 ? "Simulation Interrupted" : `E2E Inspection Pipeline: Step ${demoProgress.step}/11`}
          </h2>
          <p style={{ color: 'var(--color-warning)', fontFamily: 'var(--font-mono)', fontSize: '14px' }}>
            {demoProgress.text}
          </p>
        </div>
      )}
    </div>
  );
}
