import { useState } from 'react'
import { FileText, Zap, Loader2, Volume2, Eye, X, Ban, RotateCcw, FileCheck } from 'lucide-react'
import { useFormatChapter, useGenerateAudio, useToggleExclude } from '../hooks/useChapters'
import type { Chapter } from '../types'

interface ChapterListProps {
  chapters: Chapter[]
  bookId: string
}

interface TextModalProps {
  chapter: Chapter
  type: 'raw' | 'formatted'
  onClose: () => void
}

function TextModal({ chapter, type, onClose }: TextModalProps) {
  const isRaw = type === 'raw'
  const text = isRaw ? chapter.raw_text : chapter.formatted_text
  const title = isRaw ? 'Raw Text' : 'Formatted Text'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] mx-4 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {chapter.title || `Chapter ${chapter.chapter_number}`} - {title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-md transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {text ? (
            <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 font-mono">
              {text}
            </pre>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center">
              No {isRaw ? 'raw' : 'formatted'} text available for this chapter.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

const statusColors = {
  extracted: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  formatting: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  formatted: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  generating: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

export default function ChapterList({ chapters, bookId }: ChapterListProps) {
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
  const [modalType, setModalType] = useState<'raw' | 'formatted'>('raw')
  const [formattingChapterId, setFormattingChapterId] = useState<string | null>(null)
  const [generatingChapterId, setGeneratingChapterId] = useState<string | null>(null)
  const [excludingChapterId, setExcludingChapterId] = useState<string | null>(null)
  const formatMutation = useFormatChapter(bookId)
  const generateMutation = useGenerateAudio(bookId)
  const excludeMutation = useToggleExclude()

  const handleFormat = async (chapterId: string) => {
    setFormattingChapterId(chapterId)
    try {
      await formatMutation.mutateAsync(chapterId)
    } catch (error) {
      console.error('Format failed:', error)
    } finally {
      setFormattingChapterId(null)
    }
  }

  const handleGenerate = async (chapterId: string) => {
    setGeneratingChapterId(chapterId)
    try {
      await generateMutation.mutateAsync(chapterId)
    } catch (error) {
      console.error('Generate audio failed:', error)
    } finally {
      setGeneratingChapterId(null)
    }
  }

  const handleToggleExclude = async (chapterId: string) => {
    setExcludingChapterId(chapterId)
    try {
      await excludeMutation.mutateAsync(chapterId)
    } catch (error) {
      console.error('Toggle exclude failed:', error)
    } finally {
      setExcludingChapterId(null)
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
            className={`px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition ${
              chapter.excluded ? 'opacity-50' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4 flex-1">
                <div className={`flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${
                  chapter.excluded
                    ? 'bg-gray-200 dark:bg-gray-600'
                    : 'bg-primary-100 dark:bg-primary-900/30'
                }`}>
                  <span className={`text-lg font-bold ${
                    chapter.excluded
                      ? 'text-gray-500 dark:text-gray-400'
                      : 'text-primary-600 dark:text-primary-400'
                  }`}>
                    {chapter.chapter_number}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className={`text-lg font-semibold truncate ${
                    chapter.excluded
                      ? 'text-gray-500 dark:text-gray-400 line-through'
                      : 'text-gray-900 dark:text-white'
                  }`}>
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
                    {chapter.excluded && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300">
                        Excluded
                      </span>
                    )}
                  </div>
                  {chapter.error_message && (
                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                      Error: {chapter.error_message}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={() => handleToggleExclude(chapter.id)}
                disabled={excludingChapterId === chapter.id}
                className={`ml-4 flex items-center space-x-2 px-3 py-2 text-sm rounded-md transition ${
                  chapter.excluded
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
                title={chapter.excluded ? 'Include chapter' : 'Exclude chapter'}
              >
                {excludingChapterId === chapter.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : chapter.excluded ? (
                  <>
                    <RotateCcw className="w-4 h-4" />
                    <span>Include</span>
                  </>
                ) : (
                  <>
                    <Ban className="w-4 h-4" />
                    <span>Exclude</span>
                  </>
                )}
              </button>

              <button
                onClick={() => {
                  setModalType('raw')
                  setSelectedChapter(chapter)
                }}
                className="ml-2 flex items-center space-x-2 px-3 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-md transition"
                title="View raw text"
              >
                <Eye className="w-4 h-4" />
                <span>Raw</span>
              </button>

              {chapter.formatted_text && (
                <button
                  onClick={() => {
                    setModalType('formatted')
                    setSelectedChapter(chapter)
                  }}
                  className="ml-2 flex items-center space-x-2 px-3 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-md transition"
                  title="View formatted text"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Formatted</span>
                </button>
              )}

              {chapter.status === 'extracted' && !chapter.excluded && (
                <button
                  onClick={() => handleFormat(chapter.id)}
                  disabled={formattingChapterId === chapter.id}
                  className="ml-2 flex items-center space-x-2 px-3 py-2 text-sm bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-md transition"
                  title="Format chapter"
                >
                  {formattingChapterId === chapter.id ? (
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

              {chapter.status === 'formatted' && !chapter.excluded && (
                <button
                  onClick={() => handleGenerate(chapter.id)}
                  disabled={generatingChapterId === chapter.id}
                  className="ml-2 flex items-center space-x-2 px-3 py-2 text-sm bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-md transition"
                  title="Generate audio"
                >
                  {generatingChapterId === chapter.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Volume2 className="w-4 h-4" />
                      <span>Generate Audio</span>
                    </>
                  )}
                </button>
              )}

              {chapter.status === 'generating' && (
                <div className="ml-4 flex items-center space-x-2 text-purple-600 dark:text-purple-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="text-sm">Generating audio...</span>
                </div>
              )}

              {chapter.status === 'completed' && (
                <div className="ml-4 flex items-center space-x-2 text-green-600 dark:text-green-400">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-sm">Audio ready</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedChapter && (
        <TextModal
          chapter={selectedChapter}
          type={modalType}
          onClose={() => setSelectedChapter(null)}
        />
      )}
    </div>
  )
}
