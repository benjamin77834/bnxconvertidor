// API endpoint — compile usa local o remoto segun VITE_API_URL
const API_URL = import.meta.env.VITE_API_URL || ''

// Pipeline/Library SIEMPRE van al API Gateway de DataLab
const DATALAB_API = 'https://6lewkixco1.execute-api.us-east-1.amazonaws.com/prod'

export const COMPILE_URL = `${API_URL}/compile`
export const PIPELINE_URL = `${DATALAB_API}/pipeline`
export const PIPELINE_STATUS_URL = `${DATALAB_API}/pipeline/status`
export const PIPELINE_LOGS_URL = `${DATALAB_API}/pipeline/logs`
// Library LOCAL: el bucket S3 de DataLab esta bloqueado por una SCP de la org,
// asi que la biblioteca de grafos se guarda/sirve desde el server local.
export const LIBRARY_URL = `${API_URL}/library`
