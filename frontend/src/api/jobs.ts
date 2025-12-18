import apiClient from './client'
import type { ProcessingJob } from '../types'

export const jobsApi = {
  // Get job status
  getJob: async (jobId: string) => {
    const response = await apiClient.get<ProcessingJob>(`/jobs/${jobId}`)
    return response.data
  },

  // Get all jobs for a book
  getBookJobs: async (bookId: string) => {
    const response = await apiClient.get<ProcessingJob[]>(`/books/${bookId}/jobs`)
    return response.data
  },
}
