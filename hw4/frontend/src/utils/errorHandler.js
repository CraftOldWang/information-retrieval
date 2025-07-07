/**
 * 错误处理工具函数
 */

/**
 * 标准化API错误
 * @param {Error|Object} error - 错误对象
 * @returns {Object} - 标准化的错误对象
 */
export const normalizeError = (error) => {
  // 默认错误信息
  const defaultError = {
    message: '发生未知错误，请稍后再试',
    code: 'UNKNOWN_ERROR',
    status: 500,
    details: null
  };
  
  // 如果没有错误对象，返回默认错误
  if (!error) return defaultError;
  
  // 如果是标准Error对象
  if (error instanceof Error) {
    return {
      message: error.message || defaultError.message,
      code: error.code || defaultError.code,
      status: error.status || defaultError.status,
      details: error.details || defaultError.details
    };
  }
  
  // 如果是Axios错误响应
  if (error.response) {
    const { data, status } = error.response;
    
    // 处理后端返回的错误格式
    if (data) {
      return {
        message: data.message || data.detail || defaultError.message,
        code: data.code || `HTTP_${status}`,
        status: status || defaultError.status,
        details: data.details || null
      };
    }
    
    // 处理HTTP状态码
    return {
      message: getHttpStatusMessage(status) || defaultError.message,
      code: `HTTP_${status}`,
      status,
      details: null
    };
  }
  
  // 如果是请求错误（没有收到响应）
  if (error.request) {
    return {
      message: '无法连接到服务器，请检查网络连接',
      code: 'NETWORK_ERROR',
      status: 0,
      details: null
    };
  }
  
  // 如果是普通对象
  if (typeof error === 'object') {
    return {
      message: error.message || defaultError.message,
      code: error.code || defaultError.code,
      status: error.status || defaultError.status,
      details: error.details || defaultError.details
    };
  }
  
  // 如果是字符串
  if (typeof error === 'string') {
    return {
      message: error,
      code: defaultError.code,
      status: defaultError.status,
      details: null
    };
  }
  
  return defaultError;
};

/**
 * 获取HTTP状态码对应的错误消息
 * @param {number} status - HTTP状态码
 * @returns {string} - 错误消息
 */
const getHttpStatusMessage = (status) => {
  const statusMessages = {
    400: '请求参数错误',
    401: '未授权，请登录',
    403: '禁止访问',
    404: '请求的资源不存在',
    405: '不支持的请求方法',
    408: '请求超时',
    409: '资源冲突',
    422: '请求数据验证失败',
    429: '请求过于频繁，请稍后再试',
    500: '服务器内部错误',
    502: '网关错误',
    503: '服务不可用',
    504: '网关超时'
  };
  
  return statusMessages[status] || `HTTP错误 ${status}`;
};

/**
 * 获取用户友好的错误消息
 * @param {Error|Object} error - 错误对象
 * @returns {string} - 用户友好的错误消息
 */
export const getFriendlyErrorMessage = (error) => {
  const normalizedError = normalizeError(error);
  
  // 特定错误代码的友好消息
  const friendlyMessages = {
    'NETWORK_ERROR': '无法连接到服务器，请检查网络连接后重试',
    'HTTP_401': '登录已过期，请重新登录',
    'HTTP_403': '您没有权限执行此操作',
    'HTTP_404': '请求的资源不存在',
    'HTTP_429': '请求过于频繁，请稍后再试',
    'VALIDATION_ERROR': '输入数据验证失败，请检查输入',
    'AUTH_FAILED': '用户名或密码错误',
    'USER_EXISTS': '用户已存在',
    'INVALID_TOKEN': '无效的认证令牌',
    'TOKEN_EXPIRED': '认证已过期，请重新登录'
  };
  
  return friendlyMessages[normalizedError.code] || normalizedError.message;
};

/**
 * 记录错误到控制台
 * @param {Error|Object} error - 错误对象
 * @param {string} context - 错误上下文
 */
export const logError = (error, context = '') => {
  const normalizedError = normalizeError(error);
  
  console.error(
    `[${context}] ${normalizedError.code} (${normalizedError.status}): ${normalizedError.message}`,
    normalizedError.details || ''
  );
};