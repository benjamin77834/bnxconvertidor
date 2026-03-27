// API endpoint — in dev proxied by Vite, in prod points to Lambda Function URL
const API_URL = import.meta.env.VITE_API_URL || ''

export const COMPILE_URL = `${API_URL}/compile`
