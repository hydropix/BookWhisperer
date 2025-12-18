import apiClient from './client'
import type {
  Book,
  BookListResponse,
  UploadBookResponse,
  FormatAllChaptersResponse,
} from '../types'

export const booksApi = {
  // Get all books with pagination
  getBooks: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get<BookListResponse>('/books', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  // Get single book by ID
  getBook: async (bookId: string) => {
    const response = await apiClient.get<Book>(`/books/${bookId}`)
    return response.data
  },

  // Upload a new book
  uploadBook: async (file: File, title?: string, author?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    if (author) formData.append('author', author)

    const response = await apiClient.post<UploadBookResponse>('/books/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Delete a book
  deleteBook: async (bookId: string) => {
    const response = await apiClient.delete(`/books/${bookId}`)
    return response.data
  },

  // Start processing a book (parse)
  processBook: async (bookId: string) => {
    const response = await apiClient.post(`/books/${bookId}/process`)
    return response.data
  },

  // Format all chapters in a book
  formatAllChapters: async (bookId: string) => {
    const response = await apiClient.post<FormatAllChaptersResponse>(
      `/books/${bookId}/chapters/format`
    )
    return response.data
  },

  // Download book as ZIP
  downloadBook: async (bookId: string) => {
    const response = await apiClient.get(`/books/${bookId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },
}
