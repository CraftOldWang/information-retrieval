import axios from 'axios';
import { API_BASE_URL } from '../config';

// 创建axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}`,
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

// 基础搜索
export const search = async (query, page = 1, pageSize = 10, searchType = 'normal', filters = {}) => {
  try {
    const params = {
      q: query,
      page,
      page_size: pageSize,
      search_type: searchType,
      ...filters
    };
    
    const response = await api.get('/search', { params });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 文档搜索
export const searchDocuments = async (query, page = 1, pageSize = 10, docType = [], filters = {}) => {
  try {
    // 检测查询类型
    const queryInfo = detectQueryType(query);
    
    const params = {
      q: query,
      page,
      page_size: pageSize,
      doc_type: docType,
      search_type: queryInfo.searchType,
      ...filters
    };
    
    const response = await api.get('/search/documents', { params });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 个性化搜索
export const personalizedSearch = async (query, page = 1, pageSize = 10) => {
  try {
    const params = {
      q: query,
      page,
      page_size: pageSize
    };
    
    const response = await api.get('/search/personalized', { params });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

// 获取搜索建议
export const getSearchSuggestions = async (query, limit = 10) => {
  try {
    const params = {
      q: query,
      limit
    };
    
    const response = await api.get('/search/suggest', { params });
    return response.data.suggestions;
  } catch (error) {
    throw handleError(error);
  }
};

// 获取查询推荐
export const getQueryRecommendations = async (query, limit = 10) => {
  try {
    const params = {
      q: query,
      limit
    };
    
    const response = await api.get('/recommendations/queries', { params });
    return response.data.recommendations;
  } catch (error) {
    throw handleError(error);
  }
};

// 获取相关查询
export const getRelatedQueries = async (query, limit = 5) => {
  try {
    const params = {
      q: query,
      limit
    };
    
    const response = await api.get('/recommendations/related', { params });
    return response.data.recommendations;
  } catch (error) {
    throw handleError(error);
  }
};

// 解析搜索查询，处理特殊语法
export const parseSearchQuery = (query) => {
  // 检查是否包含文件类型过滤
  const fileTypeMatch = query.match(/filetype:(\w+)/);
  if (fileTypeMatch) {
    const fileType = fileTypeMatch[1];
    const cleanQuery = query.replace(/filetype:\w+\s*/, '').trim();
    return {
      query: cleanQuery,
      isDocumentSearch: true,
      docType: [fileType]
    };
  }
  
  // 检查是否是短语搜索（包含引号）
  if (query.includes('"')) {
    return {
      query,
      isDocumentSearch: false,
      searchType: 'phrase'
    };
  }
  
  // 检查是否是通配符搜索
  if (query.includes('*') || query.includes('?')) {
    return {
      query,
      isDocumentSearch: false,
      searchType: 'wildcard'
    };
  }
  
  // 默认普通搜索
  return {
    query,
    isDocumentSearch: false,
    searchType: 'normal'
  };
};

// 错误处理函数
const handleError = (error) => {
  if (error.response) {
    // 服务器响应错误
    const message = error.response.data.detail || error.response.data.message || '搜索服务错误';
    return new Error(message);
  } else if (error.request) {
    // 请求未收到响应
    return new Error('无法连接到搜索服务，请检查网络连接');
  } else {
    // 请求设置错误
    return new Error('请求错误: ' + error.message);
  }
};