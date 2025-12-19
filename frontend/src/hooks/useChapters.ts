import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chaptersApi } from '../api'

export const useChapters = (bookId: string | undefined) => {
  return useQuery({
    queryKey: ['chapters', bookId],
    queryFn: () => chaptersApi.getChapters(bookId!),
    enabled: !!bookId,
  })
}

export const useChapter = (chapterId: string | undefined) => {
  return useQuery({
    queryKey: ['chapter', chapterId],
    queryFn: () => chaptersApi.getChapter(chapterId!),
    enabled: !!chapterId,
  })
}

export const useFormatChapter = (bookId: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chapterId: string) => chaptersApi.formatChapter(chapterId),
    onSuccess: (_data, chapterId) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
      if (bookId) {
        queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
      }
    },
  })
}

export const useGenerateAudio = (bookId: string | undefined) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chapterId: string) => chaptersApi.generateAudio(chapterId),
    onSuccess: (_data, chapterId) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
      if (bookId) {
        queryClient.invalidateQueries({ queryKey: ['chapters', bookId] })
      }
    },
  })
}

export const useToggleExclude = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chapterId: string) => chaptersApi.toggleExclude(chapterId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', data.id] })
      queryClient.invalidateQueries({ queryKey: ['chapters', data.book_id] })
    },
  })
}
