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

export const useFormatChapter = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chapterId: string) => chaptersApi.formatChapter(chapterId),
    onSuccess: (_data, chapterId) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
    },
  })
}

export const useGenerateAudio = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chapterId: string) => chaptersApi.generateAudio(chapterId),
    onSuccess: (_data, chapterId) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
    },
  })
}
