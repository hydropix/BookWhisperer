import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'
import { jobsApi } from '../api'
import type { ProcessingJob } from '../types'

interface ProgressTrackerProps {
  bookId: string
}

export default function ProgressTracker({ bookId }: ProgressTrackerProps) {
  const queryClient = useQueryClient()

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs', bookId],
    queryFn: () => jobsApi.getBookJobs(bookId),
    refetchInterval: (query) => {
      const data = query.state.data as ProcessingJob[] | undefined
      if (!Array.isArray(data)) return false
      const hasActiveJobs = data.some(
        (job) => job.status === 'pending' || job.status === 'running'
      )
      return hasActiveJobs ? 2000 : false // Poll every 2s if active jobs
    },
  })

  // Invalidate related queries when jobs complete
  useEffect(() => {
    const allCompleted = jobs?.every((job) => job.status === 'completed' || job.status === 'failed')
    if (allCompleted && jobs && jobs.length > 0) {
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
      queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
    }
  }, [jobs, bookId, queryClient])

  if (isLoading || !Array.isArray(jobs) || jobs.length === 0) {
    return null
  }

  const activeJobs = jobs.filter((job) => job.status === 'pending' || job.status === 'running')

  if (activeJobs.length === 0) {
    return null
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Processing Status
      </h2>

      <div className="space-y-4">
        {jobs.map((job) => (
          <JobProgress key={job.id} job={job} />
        ))}
      </div>
    </div>
  )
}

function JobProgress({ job }: { job: ProcessingJob }) {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-400" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const getJobTypeLabel = (type: string) => {
    switch (type) {
      case 'parse_book':
        return 'Parsing Book'
      case 'format_chapter':
        return 'Formatting Chapter'
      case 'generate_audio':
        return 'Generating Audio'
      default:
        return type
    }
  }

  const getStatusColor = () => {
    switch (job.status) {
      case 'pending':
        return 'bg-gray-200 dark:bg-gray-600'
      case 'running':
        return 'bg-blue-600'
      case 'completed':
        return 'bg-green-600'
      case 'failed':
        return 'bg-red-600'
      default:
        return 'bg-gray-200 dark:bg-gray-600'
    }
  }

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">
              {getJobTypeLabel(job.job_type)}
            </h3>
            {job.metadata && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {job.metadata.chapter_number && `Chapter ${job.metadata.chapter_number}`}
                {job.metadata.current_chunk &&
                  job.metadata.total_chunks &&
                  ` - Chunk ${job.metadata.current_chunk}/${job.metadata.total_chunks}`}
              </p>
            )}
          </div>
        </div>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {job.progress_percent}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>

      {/* Error message */}
      {job.error_message && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{job.error_message}</p>
      )}

      {/* Retry info */}
      {job.retry_count > 0 && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Retry attempt: {job.retry_count}/{job.max_retries}
        </p>
      )}
    </div>
  )
}
