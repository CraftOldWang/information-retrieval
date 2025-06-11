import { useState, useEffect, useCallback, useContext } from 'react';
import { getSearchSuggestions } from '../services/searchService';
import { getSearchHistory } from '../services/searchService';
import { debounce } from '../utils/helpers';
import { normalizeError, logError } from '../utils/errorHandler';
import { AuthContext } from '../contexts/AuthContext';
import { SEARCH_CONFIG } from '../config';

/**
 * 搜索建议钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 建议状态和方法
 */
const useSuggestions = (options = {}) => {
  const {
    initialQuery = '',
    debounceTime = 300,
    suggestionsLimit = SEARCH_CONFIG.SUGGESTION_LIMIT,
    historyLimit = SEARCH_CONFIG.HISTORY_LIMIT,
    enabled = true
  } = options;
  
  const { currentUser } = useContext(AuthContext);
  
  // 状态
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [history, setHistory] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 加载搜索历史
  const loadSearchHistory = useCallback(async () => {
    if (!currentUser) {
      setHistory([]);
      return;
    }
    
    try {
      const response = await getSearchHistory(historyLimit);
      setHistory(response.history || []);
    } catch (err) {
      logError(err, 'SearchHistory');
      setHistory([]);
    }
  }, [currentUser, historyLimit]);
  
  // 获取搜索建议
  const fetchSuggestions = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.trim().length < 2 || !enabled) {
      setSuggestions([]);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getSearchSuggestions(searchQuery, suggestionsLimit);
      setSuggestions(response || []);
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'SearchSuggestions');
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [suggestionsLimit, enabled]);
  
  // 防抖处理的获取建议函数
  const debouncedFetchSuggestions = useCallback(
    debounce((searchQuery) => fetchSuggestions(searchQuery), debounceTime),
    [fetchSuggestions, debounceTime]
  );
  
  // 当查询变化时获取建议
  useEffect(() => {
    if (query && showSuggestions) {
      debouncedFetchSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query, showSuggestions, debouncedFetchSuggestions]);
  
  // 当用户登录状态变化时加载历史
  useEffect(() => {
    loadSearchHistory();
  }, [currentUser, loadSearchHistory]);
  
  // 处理输入变化
  const handleInputChange = useCallback((event) => {
    const newQuery = event.target.value;
    setQuery(newQuery);
    
    if (newQuery) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  }, []);
  
  // 处理建议点击
  const handleSuggestionClick = useCallback((suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    return suggestion;
  }, []);
  
  // 处理历史点击
  const handleHistoryClick = useCallback((historyItem) => {
    setQuery(historyItem.query);
    setShowSuggestions(false);
    return historyItem.query;
  }, []);
  
  // 处理输入框聚焦
  const handleInputFocus = useCallback(() => {
    if (query) {
      setShowSuggestions(true);
    }
  }, [query]);
  
  // 处理输入框失焦
  const handleInputBlur = useCallback(() => {
    // 使用延时，以便点击建议项时能够触发点击事件
    setTimeout(() => {
      setShowSuggestions(false);
    }, 200);
  }, []);
  
  // 清除查询
  const clearQuery = useCallback(() => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
  }, []);
  
  return {
    // 状态
    query,
    suggestions,
    history,
    showSuggestions,
    loading,
    error,
    
    // 方法
    setQuery,
    handleInputChange,
    handleSuggestionClick,
    handleHistoryClick,
    handleInputFocus,
    handleInputBlur,
    clearQuery,
    loadSearchHistory
  };
};

export default useSuggestions;