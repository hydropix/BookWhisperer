import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface UsePollingOptions {
  enabled: boolean
  interval?: number
  queryKey: unknown[]
}

export const usePolling = ({ enabled, interval = 2000, queryKey }: UsePollingOptions) => {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!enabled) return

    const timer = setInterval(() => {
      queryClient.invalidateQueries({ queryKey })
    }, interval)

    return () => clearInterval(timer)
  }, [enabled, interval, queryKey, queryClient])
}

export default usePolling
