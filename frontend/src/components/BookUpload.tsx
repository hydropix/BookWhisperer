import { useState, useCallback } from 'react'
import { Upload, FileText, Loader2 } from 'lucide-react'
import { useUploadBook } from '../hooks/useBooks'
import { useToast } from '../hooks/useToast'

export default function BookUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')

  const uploadMutation = useUploadBook()
  const toast = useToast()

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith('.epub') || droppedFile.name.endsWith('.txt'))) {
      setFile(droppedFile)
      // Auto-extract title from filename
      const fileName = droppedFile.name.replace(/\.(epub|txt)$/i, '')
      setTitle(fileName)
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      const fileName = selectedFile.name.replace(/\.(epub|txt)$/i, '')
      setTitle(fileName)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    try {
      await uploadMutation.mutateAsync({
        file,
        title: title || undefined,
        author: author || undefined,
      })

      toast.success('Book uploaded successfully', 'Your book is now being processed')

      // Reset form
      setFile(null)
      setTitle('')
      setAuthor('')
    } catch (error) {
      toast.error('Upload failed', 'Please check the file and try again')
      console.error('Upload failed:', error)
    }
  }

  const handleReset = () => {
    setFile(null)
    setTitle('')
    setAuthor('')
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Upload Book
      </h2>

      {!file ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition ${
            isDragging
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
          }`}
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            Drop your EPUB or TXT file here
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            or click to browse
          </p>
          <label className="inline-block">
            <input
              type="file"
              accept=".epub,.txt"
              onChange={handleFileInput}
              className="hidden"
            />
            <span className="cursor-pointer inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md transition">
              Select File
            </span>
          </label>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File preview */}
          <div className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <FileText className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            <div className="flex-1">
              <p className="font-medium text-gray-900 dark:text-white">{file.name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
            >
              Remove
            </button>
          </div>

          {/* Title input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter book title"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Author input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Author
            </label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Enter author name"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Upload button */}
          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={uploadMutation.isPending}
              className="flex-1 flex items-center justify-center px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-md transition"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Upload & Process
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              Cancel
            </button>
          </div>

          {/* Error message */}
          {uploadMutation.isError && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-sm text-red-800 dark:text-red-200">
                Upload failed. Please try again.
              </p>
            </div>
          )}

          {/* Success message */}
          {uploadMutation.isSuccess && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <p className="text-sm text-green-800 dark:text-green-200">
                Book uploaded successfully! Processing has started.
              </p>
            </div>
          )}
        </form>
      )}
    </div>
  )
}
