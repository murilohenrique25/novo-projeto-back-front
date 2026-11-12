import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import CompanyDashboard from './pages/CompanyDashboard'
import AdminDashboard from './pages/AdminDashboard'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <CompanyDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin"
                element={
                    <ProtectedRoute adminOnly>
                        <AdminDashboard />
                    </ProtectedRoute>
                }
            />
            <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
    )
}
