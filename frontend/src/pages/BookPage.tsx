import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'
import { useBook } from '../hooks/useBooks'
import { useChapters } from '../hooks/useChapters'
import BookDetails from '../components/BookDetails'
import ChapterList from '../components/ChapterList'
import ProgressTracker from '../components/ProgressTracker'
import { usePolling } from '../hooks/usePolling'

export default function BookPage() {
  const { bookId } = useParams<{ bookId: string }>()
  const navigate = useNavigate()
  const { data: book, isLoading: bookLoading, error: bookError } = useBook(bookId)
  const { data: chaptersData, isLoading: chaptersLoading } = useChapters(bookId)

  // Poll for updates when book is being processed
  const isProcessing =
    book &&
    (book.status === 'parsing' ||
      book.status === 'formatting' ||
      book.status === 'generating')

  usePolling({
    enabled: !!isProcessing,
    interval: 2000,
    queryKey: ['book', bookId],
  })

  usePolling({
    enabled: !!isProcessing,
    interval: 2000,
    queryKey: ['chapters', bookId],
  })

  if (bookLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (bookError || !book) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
          <div>
            <h3 className="font-semibold text-red-800 dark:text-red-200">Book not found</h3>
            <p className="text-sm text-red-600 dark:text-red-300">
              The book you're looking for doesn't exist.
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/')}
          className="mt-4 flex items-center space-x-2 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to home</span>
        </button>
      </div>
    )
  }

  const chapters = chaptersData?.chapters || []

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
      >
        <ArrowLeft className="w-5 h-5" />
        <span>Back to all books</span>
      </button>

      <BookDetails book={book} />

      {bookId && <ProgressTracker bookId={bookId} />}

      {chaptersLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      ) : (
        <ChapterList chapters={chapters} bookId={book.id} />
      )}
    </div>
  )
}
