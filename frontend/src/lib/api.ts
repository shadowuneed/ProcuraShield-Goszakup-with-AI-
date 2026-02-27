import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Автоматическое добавление токена
api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// === API ФУНКЦИИ ===

// Дашборд
export const fetchDashboardStats = () => api.get('/api/dashboard/stats');

// Закупки
export const fetchProcurements = (params?: Record<string, unknown>) =>
  api.get('/api/procurements', { params });

export const fetchProcurement = (id: number) =>
  api.get(`/api/procurements/${id}`);

export const searchProcurements = (query: string) =>
  api.get('/api/procurements/search', { params: { q: query } });

// Анализ
export const analyzeProcurement = (id: number) =>
  api.post(`/api/analysis/analyze/${id}`);

export const fetchAnalysisResults = (id: number) =>
  api.get(`/api/analysis/results/${id}`);

// Граф
export const fetchEntityGraph = (entityId: string) =>
  api.get(`/api/graph/entity/${entityId}`);

export const fetchCommunities = () =>
  api.get('/api/graph/communities');

// Блокчейн
export const verifyBlockchainDocument = (hash: string) =>
  api.get(`/api/blockchain/verify/${hash}`);

export const fetchBlockchainHistory = (procurementId: number) =>
  api.get(`/api/blockchain/history/${procurementId}`);

// Алерты
export const fetchAlerts = (params?: Record<string, unknown>) =>
  api.get('/api/alerts', { params });

// Информатор
export const submitWhistleblowerReport = (data: FormData) =>
  api.post('/api/whistleblower/submit', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const checkReportStatus = (trackingId: string) =>
  api.get(`/api/whistleblower/status/${trackingId}`);
