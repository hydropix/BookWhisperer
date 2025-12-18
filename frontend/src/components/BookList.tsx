import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Trash2, Loader2, AlertCircle } from 'lucide-react'
import { useBooks, useDeleteBook } from '../hooks/useBooks'
import { useToast } from '../hooks/useToast'
import { ConfirmDialog } from './ConfirmDialog'
import type { Book } from '../types'

const statusColors = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  parsing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  parsed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  formatting: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  generating: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

export default function BookList() {
  const [page, setPage] = useState(1)
  const [bookToDelete, setBookToDelete] = useState<Book | null>(null)
  const navigate = useNavigate()
  const { data, isLoading, error } = useBooks(page, 20)
  const deleteMutation = useDeleteBook()
  const toast = useToast()

  const handleDeleteClick = (book: Book, e: React.MouseEvent) => {
    e.stopPropagation()
    setBookToDelete(book)
  }

  const handleConfirmDelete = async () => {
    if (!bookToDelete) return

    try {
      await deleteMutation.mutateAsync(bookToDelete.id)
      toast.success('Book deleted', `"${bookToDelete.title}" has been removed`)
      setBookToDelete(null)
    } catch (error) {
      toast.error('Delete failed', 'Unable to delete the book. Please try again.')
      console.error('Delete failed:', error)
    }
  }

  const handleCancelDelete = () => {
    setBookToDelete(null)
  }

  const handleBookClick = (bookId: string) => {
    navigate(`/books/${bookId}`)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
          <div>
            <h3 className="font-semibold text-red-800 dark:text-red-200">
              Failed to load books
            </h3>
            <p className="text-sm text-red-600 dark:text-red-300">
              Please check your connection and try again.
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!data?.items || data.items.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
        <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No books yet
        </h3>
        <p className="text-gray-500 dark:text-gray-400">
          Upload your first book to get started
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Your Books ({data.total})
        </h2>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {data.items.map((book: Book) => (
          <div
            key={book.id}
            onClick={() => handleBookClick(book.id)}
            className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4 flex-1">
                <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                  <BookOpen className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                    {book.title}
                  </h3>
                  {book.author && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      by {book.author}
                    </p>
                  )}
                  <div className="flex items-center space-x-4 mt-2">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {book.total_chapters} chapters
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {book.file_type.toUpperCase()}
                    </span>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        statusColors[book.status]
                      }`}
                    >
                      {book.status}
                    </span>
                  </div>
                  {book.error_message && (
                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                      Error: {book.error_message}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={(e) => handleDeleteClick(book, e)}
                disabled={deleteMutation.isPending}
                className="ml-4 p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition disabled:opacity-50"
                title="Delete book"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data.pages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Page {page} of {data.pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!bookToDelete}
        title="Delete Book"
        message={
          <>
            Are you sure you want to delete <strong>"{bookToDelete?.title}"</strong>?
            <br />
            <br />
            This action cannot be undone. All chapters and associated data will be permanently removed.
          </>
        }
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
