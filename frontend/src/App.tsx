import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import Home from './pages/Home'
import BookPage from './pages/BookPage'
import { ToastProvider } from './hooks/useToast'

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition">
              <BookOpen className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  BookWhisperer
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Transform your books into audiobooks
                </p>
              </div>
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/books/:bookId" element={<BookPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-gray-500 dark:text-gray-400 text-sm">
              BookWhisperer - Powered by Ollama LLM & Chatterbox TTS
            </p>
          </div>
        </footer>
      </div>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
