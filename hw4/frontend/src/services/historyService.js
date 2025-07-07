import axios from 'axios';
import { API_BASE_URL } from '../config';

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/history`,
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

// 获取搜索历史
export const getSearchHistory = async (page = 1, pageSize = 10) => {
  try {
    const params = {
      page,
      page_size: pageSize
    };
    
    const response = await api.get('/', { params });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 删除单条搜索历史
export const deleteHistoryItem = async (historyId) => {
  try {
    const response = await api.delete(`/${historyId}`);
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 清空所有搜索历史
export const clearAllHistory = async () => {
  try {
    const response = await api.delete('/all');
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 错误处理函数
const handleError = (error) => {
  if (error.response) {
    // 服务器响应错误
    const message = error.response.data.detail || error.response.data.message || '历史服务错误';
    return new Error(message);
  } else if (error.request) {
    // 请求未收到响应
    return new Error('无法连接到服务器，请检查网络连接');
  } else {
    // 请求设置错误
    return new Error('请求错误: ' + error.message);
  }
};