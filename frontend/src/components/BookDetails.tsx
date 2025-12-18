import { useState } from 'react'
import { BookOpen, FileText, Zap, Loader2 } from 'lucide-react'
import { useFormatAllChapters } from '../hooks/useBooks'
import { useToast } from '../hooks/useToast'
import { ConfirmDialog } from './ConfirmDialog'
import type { Book } from '../types'

interface BookDetailsProps {
  book: Book
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  parsing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  parsed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  formatting: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  generating: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

export default function BookDetails({ book }: BookDetailsProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const formatMutation = useFormatAllChapters()
  const toast = useToast()

  const handleFormatClick = () => {
    setShowConfirmDialog(true)
  }

  const handleConfirmFormat = async () => {
    try {
      await formatMutation.mutateAsync(book.id)
      toast.success('Formatting started', `Processing ${book.total_chapters} chapters`)
      setShowConfirmDialog(false)
    } catch (error) {
      toast.error('Formatting failed', 'Unable to start formatting. Please try again.')
      console.error('Format failed:', error)
    }
  }

  const handleCancelFormat = () => {
    setShowConfirmDialog(false)
  }

  const canFormat = book.status === 'parsed' && book.total_chapters > 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start space-x-4">
          <div className="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
            <BookOpen className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {book.title}
            </h1>
            {book.author && (
              <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
                by {book.author}
              </p>
            )}
            <div className="flex items-center space-x-3 mt-3">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  statusColors[book.status]
                }`}
              >
                {book.status}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {book.file_type.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {canFormat && (
          <button
            onClick={handleFormatClick}
            disabled={formatMutation.isPending}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-md transition"
          >
            {formatMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Formatting...</span>
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                <span>Format All Chapters</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Chapters</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {book.total_chapters}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <BookOpen className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">File Type</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                {book.file_type.toUpperCase()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <Zap className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                {book.status}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Error message */}
      {book.error_message && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-red-800 dark:text-red-200 mb-1">Error</h3>
          <p className="text-sm text-red-600 dark:text-red-300">{book.error_message}</p>
        </div>
      )}

      {/* Metadata */}
      {book.metadata && Object.keys(book.metadata).length > 0 && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Metadata
          </h3>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(book.metadata).map(([key, value]) => (
              <div key={key}>
                <dt className="text-gray-500 dark:text-gray-400 capitalize">{key}:</dt>
                <dd className="text-gray-900 dark:text-white font-medium">
                  {String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        title="Format All Chapters"
        message={
          <>
            This will format all <strong>{book.total_chapters} chapters</strong> using the LLM.
            <br />
            <br />
            The process may take several minutes depending on the book size. You can monitor progress in the tracker below.
          </>
        }
        confirmText="Start Formatting"
        cancelText="Cancel"
        variant="info"
        onConfirm={handleConfirmFormat}
        onCancel={handleCancelFormat}
        isLoading={formatMutation.isPending}
      />
    </div>
  )
}
