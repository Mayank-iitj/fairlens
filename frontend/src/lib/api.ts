import axios from 'axios'

const rawApiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim() || '/api/v1'
const API_URL = rawApiUrl.replace(/\/+$/, '')

export const api = axios.create({
  baseURL: API_URL,
})
