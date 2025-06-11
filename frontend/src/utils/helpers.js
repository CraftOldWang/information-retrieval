/**
 * 通用辅助函数
 */

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或Date对象
 * @param {Object} options - 格式化选项
 * @returns {string} - 格式化后的日期字符串
 */
export const formatDate = (date, options = {}) => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) return '无效日期';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  const mergedOptions = { ...defaultOptions, ...options };
  
  return dateObj.toLocaleDateString('zh-CN', mergedOptions);
};

/**
 * 截断文本
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀
 * @returns {string} - 截断后的文本
 */
export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text) return '';
  
  if (text.length <= maxLength) return text;
  
  return text.substring(0, maxLength) + suffix;
};

/**
 * 高亮文本中的关键词
 * @param {string} text - 原始文本
 * @param {string|Array} keywords - 关键词或关键词数组
 * @param {string} highlightClass - 高亮CSS类名
 * @returns {string} - 包含高亮HTML的文本
 */
export const highlightKeywords = (text, keywords, highlightClass = 'highlight') => {
  if (!text || !keywords) return text;
  
  const keywordArray = Array.isArray(keywords) ? keywords : [keywords];
  
  let result = text;
  
  keywordArray.forEach(keyword => {
    if (!keyword) return;
    
    const regex = new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    result = result.replace(regex, match => `<span class="${highlightClass}">${match}</span>`);
  });
  
  return result;
};

/**
 * 格式化URL（移除协议，截断过长URL）
 * @param {string} url - 原始URL
 * @param {number} maxLength - 最大长度
 * @returns {string} - 格式化后的URL
 */
export const formatUrl = (url, maxLength = 50) => {
  if (!url) return '';
  
  // 移除协议
  let formatted = url.replace(/^https?:\/\//i, '');
  
  // 移除尾部斜杠
  formatted = formatted.replace(/\/$/, '');
  
  // 截断过长URL
  if (formatted.length > maxLength) {
    const firstPart = formatted.substring(0, Math.floor(maxLength / 2));
    const lastPart = formatted.substring(formatted.length - Math.floor(maxLength / 3));
    formatted = `${firstPart}...${lastPart}`;
  }
  
  return formatted;
};

/**
 * 获取网站图标URL
 * @param {string} url - 网站URL
 * @returns {string} - 图标URL
 */
export const getFaviconUrl = (url) => {
  if (!url) return '';
  
  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
    return `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=32`;
  } catch (e) {
    return '';
  }
};

/**
 * 解析查询字符串
 * @param {string} queryString - 查询字符串
 * @returns {Object} - 解析后的参数对象
 */
export const parseQueryString = (queryString) => {
  const params = {};
  
  if (!queryString || typeof queryString !== 'string') return params;
  
  // 移除开头的 ? 或 #
  const query = queryString.replace(/^[?#]/, '');
  
  // 分割参数
  const pairs = query.split('&');
  
  for (let i = 0; i < pairs.length; i++) {
    const pair = pairs[i].split('=');
    const key = decodeURIComponent(pair[0] || '');
    
    if (!key) continue;
    
    params[key] = decodeURIComponent(pair[1] || '');
  }
  
  return params;
};

/**
 * 构建查询字符串
 * @param {Object} params - 参数对象
 * @returns {string} - 查询字符串
 */
export const buildQueryString = (params) => {
  if (!params || typeof params !== 'object') return '';
  
  const parts = [];
  
  for (const key in params) {
    if (Object.prototype.hasOwnProperty.call(params, key) && params[key] !== undefined && params[key] !== null) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
    }
  }
  
  return parts.length > 0 ? `?${parts.join('&')}` : '';
};

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} - 防抖处理后的函数
 */
export const debounce = (func, wait = 300) => {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * 节流函数
 * @param {Function} func - 要执行的函数
 * @param {number} limit - 限制时间（毫秒）
 * @returns {Function} - 节流处理后的函数
 */
export const throttle = (func, limit = 300) => {
  let inThrottle;
  
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
};