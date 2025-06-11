/**
 * 搜索相关工具函数
 */
import { DOCUMENT_TYPES, SEARCH_TYPES } from '../config';

/**
 * 解析搜索查询
 * @param {string} query - 搜索查询
 * @returns {Object} - 解析结果
 */
export const parseSearchQuery = (query) => {
  if (!query) return { query: '', type: 'normal', isDocumentSearch: false };
  
  // 检查是否包含文件类型过滤
  const fileTypeMatch = query.match(/filetype:(\w+)/);
  if (fileTypeMatch) {
    const fileType = fileTypeMatch[1];
    const cleanQuery = query.replace(/filetype:\w+\s*/, '').trim();
    
    // 验证文件类型是否有效
    const isValidFileType = DOCUMENT_TYPES.some(type => type.value === fileType);
    
    return {
      query: cleanQuery,
      type: 'normal',
      isDocumentSearch: true,
      docType: isValidFileType ? [fileType] : []
    };
  }
  
  // 检查是否是站点搜索
  const siteMatch = query.match(/site:([\w.-]+)/);
  if (siteMatch) {
    const site = siteMatch[1];
    const cleanQuery = query.replace(/site:[\w.-]+\s*/, '').trim();
    
    return {
      query: cleanQuery,
      type: 'normal',
      isDocumentSearch: false,
      filters: { site }
    };
  }
  
  // 检查是否是短语搜索（包含引号）
  if (query.includes('"')) {
    return {
      query,
      type: 'phrase',
      isDocumentSearch: false
    };
  }
  
  // 检查是否是通配符搜索
  if (query.includes('*') || query.includes('?')) {
    return {
      query,
      type: 'wildcard',
      isDocumentSearch: false
    };
  }
  
  // 默认普通搜索
  return {
    query,
    type: 'normal',
    isDocumentSearch: false
  };
};

/**
 * 构建搜索过滤器参数
 * @param {Object} filters - 过滤器对象
 * @returns {Object} - 处理后的过滤器参数
 */
export const buildSearchFilters = (filters) => {
  if (!filters || typeof filters !== 'object') return {};
  
  const result = {};
  
  // 处理时间范围
  if (filters.startDate) {
    result.start_date = filters.startDate;
  }
  
  if (filters.endDate) {
    result.end_date = filters.endDate;
  }
  
  // 处理站点过滤
  if (filters.site) {
    result.site = filters.site;
  }
  
  // 处理文档类型
  if (filters.docType && Array.isArray(filters.docType) && filters.docType.length > 0) {
    result.doc_type = filters.docType.join(',');
  }
  
  // 处理语言过滤
  if (filters.language) {
    result.language = filters.language;
  }
  
  return result;
};

/**
 * 获取搜索类型标签
 * @param {string} type - 搜索类型值
 * @returns {string} - 搜索类型标签
 */
export const getSearchTypeLabel = (type) => {
  const searchType = SEARCH_TYPES.find(item => item.value === type);
  return searchType ? searchType.label : '普通搜索';
};

/**
 * 获取文档类型标签
 * @param {string} type - 文档类型值
 * @returns {string} - 文档类型标签
 */
export const getDocumentTypeLabel = (type) => {
  const docType = DOCUMENT_TYPES.find(item => item.value === type);
  return docType ? docType.label : type;
};

/**
 * 格式化搜索结果数量和时间
 * @param {number} resultCount - 结果数量
 * @param {number} searchTime - 搜索时间（毫秒）
 * @returns {string} - 格式化后的字符串
 */
export const formatSearchStats = (resultCount, searchTime) => {
  const count = typeof resultCount === 'number' ? resultCount : 0;
  const time = typeof searchTime === 'number' ? searchTime / 1000 : 0;
  
  return `找到约 ${count.toLocaleString()} 条结果（用时 ${time.toFixed(2)} 秒）`;
};

/**
 * 从URL中提取搜索参数
 * @param {Object} queryParams - URL查询参数
 * @returns {Object} - 搜索参数
 */
export const extractSearchParams = (queryParams) => {
  const result = {
    query: queryParams.q || '',
    page: parseInt(queryParams.page, 10) || 1,
    type: queryParams.type || 'normal',
    filters: {}
  };
  
  // 提取文档类型
  if (queryParams.doc_type) {
    result.filters.docType = queryParams.doc_type.split(',');
  }
  
  // 提取日期范围
  if (queryParams.start_date) {
    result.filters.startDate = queryParams.start_date;
  }
  
  if (queryParams.end_date) {
    result.filters.endDate = queryParams.end_date;
  }
  
  // 提取站点
  if (queryParams.site) {
    result.filters.site = queryParams.site;
  }
  
  // 提取语言
  if (queryParams.language) {
    result.filters.language = queryParams.language;
  }
  
  return result;
};