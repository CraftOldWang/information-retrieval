import axios from 'axios';
import { API_BASE_URL } from '../config';

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/snapshots`,
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

// 获取网页快照
export const getSnapshot = async (urlId, timestamp = null) => {
  try {
    const params = timestamp ? { timestamp } : {};
    
    // 使用responseType: 'text'获取HTML内容
    const response = await api.get(`/${urlId}`, { 
      params,
      responseType: 'text'
    });
    
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 错误处理函数
const handleError = (error) => {
  if (error.response) {
    // 服务器响应错误
    if (error.response.status === 404) {
      return new Error('快照不存在');
    }
    const message = error.response.data.detail || error.response.data.message || '快照服务错误';
    return new Error(message);
  } else if (error.request) {
    // 请求未收到响应
    return new Error('无法连接到服务器，请检查网络连接');
  } else {
    // 请求设置错误
    return new Error('请求错误: ' + error.message);
  }
};