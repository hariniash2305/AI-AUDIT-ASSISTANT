import { useState, useEffect } from "react";
import axios from "axios";

// Inline SVG Icons
const Cloud = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>;
const CheckCircle = () => <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>;
const AlertCircle = () => <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>;
const TrendingUp = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>;
const RefreshCw = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>;
const Upload = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>;

function App() {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    setRefreshing(true);
    try {
      const [statsRes, findingsRes] = await Promise.all([
        axios.get("http://127.0.0.1:8000/api/stats"),
        axios.get("http://127.0.0.1:8000/api/findings")
      ]);
      setStats(statsRes.data);
      setFindings(findingsRes.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file");

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/upload",
        formData
      );

      setUploadResult(res.data);
      fetchDashboardData();
      setFile(null);
      // Reset file input
      document.querySelector('input[type="file"]').value = '';
    } catch (err) {
      console.error(err);
      alert("Upload failed. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: '#F8FAFC' }}>
      {/* Sidebar */}
      <div className="w-64 border-r flex-shrink-0" style={{ backgroundColor: '#1E3A8A', color: 'white' }}>
        <div className="p-6 flex items-center gap-3 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-white/10">
            <CheckCircle className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Audit Assistant</h1>
            <p className="text-xs opacity-75">AI-powered compliance</p>
          </div>
        </div>

        <div className="p-4">
          <div className="px-3 py-2 text-xs font-semibold uppercase tracking-widest opacity-60 mb-2">MAIN</div>
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-white/10 text-white font-medium">
            <TrendingUp className="w-5 h-5" />
            Dashboard
          </div>
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-white/10 transition-colors mt-1 text-white/80">
            <Cloud className="w-5 h-5" />
            Uploads
          </div>
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-white/10 transition-colors mt-1 text-white/80">
            <AlertCircle className="w-5 h-5" />
            Findings
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1">
        {/* Header */}
        <div className="sticky top-0 z-50 backdrop-blur-xl border-b" style={{ backgroundColor: 'white', borderColor: '#E2E8F0' }}>
          <div className="max-w-7xl mx-auto px-8 py-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-semibold" style={{ color: '#1E293B' }}>Compliance Dashboard</h2>
            </div>
            
            <button
              onClick={fetchDashboardData}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors hover:bg-gray-100 disabled:opacity-50"
              style={{ color: '#1E293B' }}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-8 py-10">
          {/* Upload Section */}
          <div className="mb-12">
            <div className="rounded-3xl overflow-hidden shadow-sm" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
              {/* Upload Header */}
              <div className="px-8 py-7" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%)' }}>
                <div className="flex items-center gap-3 mb-1">
                  <Cloud className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-semibold text-white">Upload Document</h2>
                </div>
                <p className="text-blue-100 text-sm">Add a PDF invoice or document for AI-powered audit analysis</p>
              </div>

              {/* Upload Content */}
              <div className="px-8 py-10">
                {!uploadResult ? (
                  <div className="space-y-6">
                    <div className="relative">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="absolute inset-0 opacity-0 cursor-pointer w-full"
                      />
                      <div className="border-2 border-dashed rounded-2xl p-12 text-center transition-all hover:border-blue-300" 
                           style={{ 
                             borderColor: file ? '#2563EB' : '#E2E8F0', 
                             backgroundColor: file ? '#F0F9FF' : 'transparent' 
                           }}>
                        <Upload className="w-12 h-12 mx-auto mb-4" style={{ color: '#64748B' }} />
                        <p className="font-semibold text-lg" style={{ color: '#1E293B' }}>
                          {file ? file.name : "Drop your PDF here or click to browse"}
                        </p>
                        <p className="text-sm mt-2" style={{ color: '#64748B' }}>PDF files only • Max 50MB</p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={handleUpload}
                        disabled={loading || !file}
                        className="flex-1 text-white px-8 py-4 rounded-2xl font-semibold transition-all flex items-center justify-center gap-3 disabled:opacity-60 shadow-sm"
                        style={{ backgroundColor: '#2563EB' }}
                      >
                        {loading ? (
                          <>
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Processing Document...
                          </>
                        ) : (
                          <>
                            <Upload className="w-5 h-5" />
                            Upload & Analyze
                          </>
                        )}
                      </button>
                      {file && (
                        <button
                          onClick={() => {
                            setFile(null);
                            document.querySelector('input[type="file"]').value = '';
                          }}
                          className="px-8 py-4 rounded-2xl font-medium transition-colors"
                          style={{ color: '#64748B', backgroundColor: '#F1F5F9' }}
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-5 py-4">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#F0FDF4' }}>
                      <CheckCircle className="w-8 h-8" style={{ color: '#22C55E' }} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-lg" style={{ color: '#1E293B' }}>Upload successful</p>
                      <p className="text-sm" style={{ color: '#64748B' }}>
                        {uploadResult.document_type} • AI analysis complete
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setUploadResult(null);
                        setFile(null);
                        document.querySelector('input[type="file"]').value = '';
                      }}
                      className="px-6 py-3 rounded-2xl text-sm font-medium transition-colors"
                      style={{ color: '#1E293B', backgroundColor: '#F1F5F9' }}
                    >
                      Upload Another
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* KPI Cards */}
          {stats && (
            <div className="mb-12">
              <h3 className="text-xs font-semibold uppercase tracking-widest mb-5" style={{ color: '#64748B' }}>OVERVIEW</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Documents Processed */}
                <div className="rounded-3xl p-7" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
                  <div className="flex items-start justify-between mb-6">
                    <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#F1F5F9' }}>
                      <TrendingUp className="w-6 h-6" style={{ color: '#2563EB' }} />
                    </div>
                  </div>
                  <p className="text-sm font-medium mb-1" style={{ color: '#64748B' }}>Documents Processed</p>
                  <p className="text-4xl font-bold tracking-tight" style={{ color: '#1E293B' }}>{stats.documents_processed}</p>
                </div>

                {/* Total Findings */}
                <div className="rounded-3xl p-7" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
                  <div className="flex items-start justify-between mb-6">
                    <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#F1F5F9' }}>
                      <AlertCircle className="w-6 h-6" style={{ color: '#64748B' }} />
                    </div>
                  </div>
                  <p className="text-sm font-medium mb-1" style={{ color: '#64748B' }}>Total Findings</p>
                  <p className="text-4xl font-bold tracking-tight" style={{ color: '#1E293B' }}>{stats.total_findings}</p>
                </div>

                {/* High Risk */}
                <div className="rounded-3xl p-7" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
                  <div className="flex items-start justify-between mb-6">
                    <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#FEF2F2' }}>
                      <AlertCircle className="w-6 h-6" style={{ color: '#EF4444' }} />
                    </div>
                  </div>
                  <p className="text-sm font-medium mb-1" style={{ color: '#64748B' }}>High Risk</p>
                  <p className="text-4xl font-bold tracking-tight" style={{ color: '#EF4444' }}>{stats.high_risk}</p>
                </div>

                {/* Medium Risk */}
                <div className="rounded-3xl p-7" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
                  <div className="flex items-start justify-between mb-6">
                    <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{ backgroundColor: '#FEFCE8' }}>
                      <AlertCircle className="w-6 h-6" style={{ color: '#F59E0B' }} />
                    </div>
                  </div>
                  <p className="text-sm font-medium mb-1" style={{ color: '#64748B' }}>Medium Risk</p>
                  <p className="text-4xl font-bold tracking-tight" style={{ color: '#F59E0B' }}>{stats.medium_risk}</p>
                </div>
              </div>
            </div>
          )}

          {/* Findings Table */}
          <div className="rounded-3xl overflow-hidden shadow-sm" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
            <div className="px-8 py-7 border-b flex items-center justify-between" style={{ borderColor: '#E2E8F0' }}>
              <div>
                <h3 className="text-xl font-semibold" style={{ color: '#1E293B' }}>Audit Findings</h3>
                <p className="text-sm mt-1" style={{ color: '#64748B' }}>
                  {findings.length} finding{findings.length !== 1 ? 's' : ''} detected
                </p>
              </div>
            </div>

            {findings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b" style={{ borderColor: '#E2E8F0', backgroundColor: '#F8FAFC' }}>
                      <th className="px-8 py-5 text-left text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748B' }}>
                        Rule
                      </th>
                      <th className="px-8 py-5 text-left text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748B' }}>
                        Description
                      </th>
                      <th className="px-8 py-5 text-center text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748B' }}>
                        Risk Level
                      </th>
                      <th className="px-8 py-5 text-right text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748B' }}>
                        Financial Impact
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y" style={{ borderColor: '#E2E8F0' }}>
                    {findings.map((finding) => {
                      const getRiskStyle = (level) => {
                        switch (level) {
                          case "HIGH":
                            return { bg: '#FEF2F2', text: '#EF4444', border: '#FECACA' };
                          case "MEDIUM":
                            return { bg: '#FEFBEB', text: '#F59E0B', border: '#FDE68A' };
                          default:
                            return { bg: '#F0FDF4', text: '#22C55E', border: '#BBF7D0' };
                        }
                      };
                      const style = getRiskStyle(finding.risk_level);
                      return (
                        <tr
                          key={finding.id}
                          className="hover:bg-slate-50 transition-colors"
                          style={{ backgroundColor: style.bg }}
                        >
                          <td className="px-8 py-6 font-medium" style={{ color: '#1E293B' }}>
                            {finding.rule_name}
                          </td>
                          <td className="px-8 py-6 text-sm" style={{ color: '#334155' }}>
                            {finding.description}
                          </td>
                          <td className="px-8 py-6 text-center">
                            <span
                              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold"
                              style={{ color: style.text, backgroundColor: 'white', border: `1px solid ${style.border}` }}
                            >
                              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: style.text }} />
                              {finding.risk_level}
                            </span>
                          </td>
                          <td className="px-8 py-6 text-right font-semibold" style={{ color: '#1E293B' }}>
                            {finding.difference ? (
                              <span style={{ color: finding.difference > 0 ? '#EF4444' : '#22C55E' }}>
                                ₹{Math.abs(finding.difference).toLocaleString()}
                              </span>
                            ) : (
                              <span style={{ color: '#94A3B8' }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="px-8 py-20 text-center">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ backgroundColor: '#F1F5F9' }}>
                  <Cloud className="w-8 h-8" style={{ color: '#94A3B8' }} />
                </div>
                <p className="font-semibold text-lg mb-1" style={{ color: '#1E293B' }}>No findings yet</p>
                <p className="text-sm max-w-sm mx-auto" style={{ color: '#64748B' }}>Upload documents to start receiving AI-powered compliance insights</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;