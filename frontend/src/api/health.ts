import apiClient from './client'
import type { HealthCheck, AllHealthChecks } from '../types'

export const healthApi = {
  // Check API health
  checkHealth: async () => {
    const response = await apiClient.get<HealthCheck>('/health')
    return response.data
  },

  // Check all services health
  checkAllHealth: async () => {
    const response = await apiClient.get<AllHealthChecks>('/health/all')
    return response.data
  },

  // Check Ollama health
  checkOllama: async () => {
    const response = await apiClient.get<HealthCheck>('/health/ollama')
    return response.data
  },

  // Check TTS health
  checkTTS: async () => {
    const response = await apiClient.get<HealthCheck>('/health/tts')
    return response.data
  },
}
