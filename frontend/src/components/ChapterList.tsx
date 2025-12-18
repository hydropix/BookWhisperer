import { FileText, Zap, Loader2 } from 'lucide-react'
import { useFormatChapter } from '../hooks/useChapters'
import type { Chapter } from '../types'

interface ChapterListProps {
  chapters: Chapter[]
  bookId: string
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  formatting: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  formatted: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  generating: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

export default function ChapterList({ chapters, bookId }: ChapterListProps) {
  const formatMutation = useFormatChapter()

  const handleFormat = async (chapterId: string) => {
    try {
      await formatMutation.mutateAsync(chapterId)
    } catch (error) {
      console.error('Format failed:', error)
    }
  }

  if (!chapters || chapters.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
        <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No chapters yet
        </h3>
        <p className="text-gray-500 dark:text-gray-400">
          Book is being parsed. Chapters will appear here shortly.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Chapters ({chapters.length})
        </h2>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {chapters.map((chapter) => (
          <div
            key={chapter.id}
            className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4 flex-1">
                <div className="flex-shrink-0 w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                  <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
                    {chapter.chapter_number}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                    {chapter.title || `Chapter ${chapter.chapter_number}`}
                  </h3>
                  <div className="flex items-center space-x-4 mt-2">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {chapter.word_count.toLocaleString()} words
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {chapter.character_count.toLocaleString()} chars
                    </span>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        statusColors[chapter.status]
                      }`}
                    >
                      {chapter.status}
                    </span>
                  </div>
                  {chapter.error_message && (
                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                      Error: {chapter.error_message}
                    </p>
                  )}
                </div>
              </div>

              {chapter.status === 'pending' && (
                <button
                  onClick={() => handleFormat(chapter.id)}
                  disabled={formatMutation.isPending}
                  className="ml-4 flex items-center space-x-2 px-3 py-2 text-sm bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-md transition"
                  title="Format chapter"
                >
                  {formatMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      <span>Format</span>
                    </>
                  )}
                </button>
              )}

              {chapter.status === 'formatting' && (
                <div className="ml-4 flex items-center space-x-2 text-yellow-600 dark:text-yellow-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm">Processing...</span>
                </div>
              )}

              {chapter.status === 'formatted' && (
                <div className="ml-4 flex items-center space-x-2 text-green-600 dark:text-green-400">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-sm">Ready</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
