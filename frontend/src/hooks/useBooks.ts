import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { booksApi } from '../api'
import type { Book } from '../types'

export const useBooks = (page = 1, pageSize = 20) => {
  return useQuery({
    queryKey: ['books', page, pageSize],
    queryFn: () => booksApi.getBooks(page, pageSize),
  })
}

export const useBook = (bookId: string | undefined) => {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => booksApi.getBook(bookId!),
    enabled: !!bookId,
  })
}

export const useUploadBook = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, title, author }: { file: File; title?: string; author?: string }) =>
      booksApi.uploadBook(file, title, author),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] })
    },
  })
}

export const useDeleteBook = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bookId: string) => booksApi.deleteBook(bookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] })
    },
  })
}

export const useProcessBook = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bookId: string) => booksApi.processBook(bookId),
    onSuccess: (_data, bookId) => {
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
      queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
    },
  })
}

export const useFormatAllChapters = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bookId: string) => booksApi.formatAllChapters(bookId),
    onSuccess: (_data, bookId) => {
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
      queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
    },
  })
}

export const useGenerateAllAudio = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bookId: string) => booksApi.generateAllAudio(bookId),
    onSuccess: (_data, bookId) => {
      queryClient.invalidateQueries({ queryKey: ['book', bookId] })
      queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
    },
  })
}
