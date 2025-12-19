import apiClient from './client'
import type { Chapter, ChapterListResponse, FormatChapterResponse } from '../types'

export const chaptersApi = {
  // Get all chapters for a book
  getChapters: async (bookId: string) => {
    const response = await apiClient.get<ChapterListResponse>(`/books/${bookId}/chapters`)
    return response.data
  },

  // Get single chapter
  getChapter: async (chapterId: string) => {
    const response = await apiClient.get<Chapter>(`/chapters/${chapterId}`)
    return response.data
  },

  // Format a single chapter
  formatChapter: async (chapterId: string) => {
    const response = await apiClient.post<FormatChapterResponse>(
      `/chapters/${chapterId}/format`
    )
    return response.data
  },

  // Generate audio for a chapter
  generateAudio: async (chapterId: string) => {
    const response = await apiClient.post(`/chapters/${chapterId}/generate`)
    return response.data
  },

  // Toggle chapter exclusion
  toggleExclude: async (chapterId: string) => {
    const response = await apiClient.patch<Chapter>(`/chapters/${chapterId}/exclude`)
    return response.data
  },
}
