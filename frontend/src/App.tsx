import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { LogOut, BookOpen, ShieldCheck } from 'lucide-react';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Placeholder dashboard view for Phase 1 testing
const DocumentsPlaceholder: React.FC = () => {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-6 w-6 text-indigo-600 mr-2" />
              <span className="font-semibold text-lg text-slate-900">AI Mentor</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600">{user?.email}</span>
              <button
                onClick={() => signOut()}
                className="inline-flex items-center px-3 py-1.5 border border-slate-300 text-xs font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none"
              >
                <LogOut className="h-3.5 w-3.5 mr-1" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center max-w-xl mx-auto">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <ShieldCheck className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-medium text-slate-900">Phase 1: Auth & Connectivity Verified</h3>
          <p className="mt-2 text-sm text-slate-500">
            You are securely authenticated as <span className="font-mono text-indigo-600">{user?.email}</span>.
            The JWT token is active and ready to communicate with the FastAPI backend.
          </p>
          <div className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-400">
            Phase 2 will unlock PDF upload, page-aware chunking, and PyMuPDF text extraction.
          </div>
        </div>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DocumentsPlaceholder />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/documents" replace />} />
          <Route path="*" element={<Navigate to="/documents" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;

