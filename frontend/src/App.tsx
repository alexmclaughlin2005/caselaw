import { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import DataManagement from './pages/DataManagement'
import Dockets from './pages/Dockets'
import Opinions from './pages/Opinions'
import ImportMonitor from './pages/ImportMonitor'

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  )
}

function Navigation() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/dockets', label: 'Dockets' },
    { path: '/opinions', label: 'Opinions' },
    { path: '/data', label: 'Data Management' },
    { path: '/monitor', label: 'Import Monitor' },
  ]
  
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                location.pathname === item.path
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900">
              CourtListener Database Browser
            </h1>
          </div>
        </header>
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={
                <div className="px-4 py-6">
                  <h2 className="text-2xl font-semibold mb-4">Welcome</h2>
                  <p className="text-gray-600 mb-4">
                    CourtListener Database Browser allows you to download, import, and browse
                    legal data from CourtListener's bulk data repository.
                  </p>
                  <div className="mt-6 flex gap-4">
                    <Link
                      to="/dockets"
                      className="inline-block bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Browse Dockets
                    </Link>
                    <Link
                      to="/opinions"
                      className="inline-block bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700 transition-colors"
                    >
                      Browse Opinions
                    </Link>
                    <Link
                      to="/data"
                      className="inline-block bg-gray-600 text-white px-6 py-3 rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Data Management
                    </Link>
                  </div>
                </div>
              } />
              <Route path="/dockets" element={<Dockets />} />
              <Route path="/opinions" element={<Opinions />} />
              <Route path="/data" element={<DataManagement />} />
              <Route path="/monitor" element={<ImportMonitor />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

export default App

