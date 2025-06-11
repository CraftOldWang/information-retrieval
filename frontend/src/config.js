// 全局配置文件

// API基础URL
export const API_BASE_URL = 'http://localhost:8000/api/v1';

// 搜索配置
export const SEARCH_CONFIG = {
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  SUGGESTION_LIMIT: 10,
  HISTORY_LIMIT: 10
};

// 文档类型
export const DOCUMENT_TYPES = [
  { value: 'pdf', label: 'PDF文档' },
  { value: 'doc', label: 'Word文档 (DOC)' },
  { value: 'docx', label: 'Word文档 (DOCX)' },
  { value: 'ppt', label: 'PowerPoint (PPT)' },
  { value: 'pptx', label: 'PowerPoint (PPTX)' },
  { value: 'xls', label: 'Excel表格 (XLS)' },
  { value: 'xlsx', label: 'Excel表格 (XLSX)' },
  { value: 'txt', label: '文本文件 (TXT)' }
];

// 搜索类型
export const SEARCH_TYPES = [
  { value: 'normal', label: '普通搜索' },
  { value: 'phrase', label: '短语搜索' },
  { value: 'wildcard', label: '通配符搜索' }
];

// 用户反馈类型
export const FEEDBACK_TYPES = [
  { value: 'click', label: '点击' },
  { value: 'bookmark', label: '收藏' },
  { value: 'like', label: '喜欢' },
  { value: 'dislike', label: '不喜欢' }
];