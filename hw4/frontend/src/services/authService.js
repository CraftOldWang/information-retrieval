import axios from 'axios';
import { API_BASE_URL } from '../config';

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/users`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器，添加认证令牌
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 用户登录
export const loginUser = async (username, password) => {
  try {
    const response = await api.post('/login', { username, password });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 用户注册
export const registerUser = async (userData) => {
  try {
    const response = await api.post('/register', userData);
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 获取用户资料
export const getUserProfile = async () => {
  try {
    const response = await api.get('/me');
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 获取用户偏好设置
export const getUserPreferences = async () => {
  try {
    const response = await api.get('/preferences');
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 更新用户偏好设置
export const updateUserPreferences = async (preferences) => {
  try {
    const response = await api.post('/preferences', preferences);
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 提交搜索结果反馈
export const submitFeedback = async (queryId, url, action) => {
  try {
    const response = await api.post('/feedback', { query_id: queryId, url, action });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 错误处理函数
const handleError = (error) => {
  if (error.response) {
    // 服务器响应错误
    const message = error.response.data.detail || error.response.data.message || '服务器错误';
    return new Error(message);
  } else if (error.request) {
    // 请求未收到响应
    return new Error('无法连接到服务器，请检查网络连接');
  } else {
    // 请求设置错误
    return new Error('请求错误: ' + error.message);
  }
};