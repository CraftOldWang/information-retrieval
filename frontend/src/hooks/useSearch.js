import { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { searchWeb, searchDocuments, getRelatedQueries, submitResultFeedback } from '../services/searchService';
import { parseSearchQuery, buildSearchFilters, extractSearchParams } from '../utils/searchUtils';
import { buildQueryString, parseQueryString } from '../utils/helpers';
import { normalizeError, logError } from '../utils/errorHandler';
import { AuthContext } from '../contexts/AuthContext';
import { SEARCH_CONFIG } from '../config';

/**
 * 搜索钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 搜索状态和方法
 */
const useSearch = (options = {}) => {
  const {
    initialQuery = '',
    initialPage = 1,
    initialType = 'normal',
    initialFilters = {},
    isDocumentSearch = false,
    autoSearch = true
  } = options;
  
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  // 从URL获取搜索参数
  const queryParams = parseQueryString(location.search);
  const urlSearchParams = extractSearchParams(queryParams);
  
  // 状态
  const [query, setQuery] = useState(urlSearchParams.query || initialQuery);
  const [page, setPage] = useState(urlSearchParams.page || initialPage);
  const [searchType, setSearchType] = useState(urlSearchParams.type || initialType);
  const [filters, setFilters] = useState({ ...initialFilters, ...urlSearchParams.filters });
  const [results, setResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [relatedQueries, setRelatedQueries] = useState([]);
  const [personalized, setPersonalized] = useState(!!currentUser);
  
  // 执行搜索
  const executeSearch = useCallback(async () => {
    if (!query) {
      setResults([]);
      setTotalResults(0);
      setTotalPages(0);
      setSearchTime(0);
      setError(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const searchParams = {
        page,
        pageSize: SEARCH_CONFIG.DEFAULT_PAGE_SIZE,
        personalized: personalized && !!currentUser,
        filters: buildSearchFilters(filters)
      };
      
      let response;
      
      if (isDocumentSearch) {
        // 文档搜索
        response = await searchDocuments(query, {
          ...searchParams,
          docType: filters.docType || []
        });
      } else {
        // 网页搜索
        response = await searchWeb(query, searchParams);
      }
      
      setResults(response.results || []);
      setTotalResults(response.total || 0);
      setTotalPages(response.total_pages || 0);
      setSearchTime(response.search_time || 0);
      
      // 获取相关查询
      if (response.results && response.results.length > 0) {
        try {
          const relatedResponse = await getRelatedQueries(query);
          setRelatedQueries(relatedResponse.queries || []);
        } catch (relatedError) {
          console.warn('获取相关查询失败:', relatedError);
          setRelatedQueries([]);
        }
      }
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'Search');
    } finally {
      setLoading(false);
    }
  }, [query, page, searchType, filters, personalized, currentUser, isDocumentSearch]);
  
  // 当URL参数变化时更新状态
  useEffect(() => {
    if (location.search) {
      const urlParams = extractSearchParams(queryParams);
      
      if (urlParams.query !== query) setQuery(urlParams.query || '');
      if (urlParams.page !== page) setPage(urlParams.page || 1);
      if (urlParams.type !== searchType) setSearchType(urlParams.type || 'normal');
      
      // 只更新存在的过滤器，保留其他过滤器不变
      if (Object.keys(urlParams.filters).length > 0) {
        setFilters(prevFilters => ({
          ...prevFilters,
          ...urlParams.filters
        }));
      }
    }
  }, [location.search, queryParams]);
  
  // 自动执行搜索
  useEffect(() => {
    if (autoSearch && query) {
      executeSearch();
      
      // 更新URL
      const searchParams = {
        q: query,
        page: page > 1 ? page : undefined,
        type: searchType !== 'normal' ? searchType : undefined,
        ...buildSearchFilters(filters)
      };
      
      const queryString = buildQueryString(searchParams);
      const currentPath = location.pathname;
      const newUrl = `${currentPath}${queryString}`;
      
      // 只有当URL真的变化时才导航
      if (location.search !== queryString) {
        navigate(newUrl, { replace: true });
      }
    }
  }, [query, page, searchType, filters, personalized, autoSearch, executeSearch, navigate, location.pathname, location.search]);
  
  // 处理搜索提交
  const handleSearch = useCallback((newQuery, newType = searchType) => {
    if (newQuery === query && newType === searchType) {
      // 如果查询和类型没变，但页码不是1，重置页码并重新搜索
      if (page !== 1) {
        setPage(1);
      } else {
        // 否则直接重新搜索
        executeSearch();
      }
    } else {
      // 查询或类型变化，重置页码并更新查询和类型
      setQuery(newQuery);
      setSearchType(newType);
      setPage(1);
    }
  }, [query, searchType, page, executeSearch]);
  
  // 处理页码变化
  const handlePageChange = useCallback((newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  }, [totalPages]);
  
  // 处理过滤器变化
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(prevFilters => ({
      ...prevFilters,
      ...newFilters
    }));
    setPage(1); // 重置页码
  }, []);
  
  // 处理搜索类型变化
  const handleTypeChange = useCallback((newType) => {
    setSearchType(newType);
    setPage(1); // 重置页码
  }, []);
  
  // 处理个性化搜索切换
  const handlePersonalizedToggle = useCallback(() => {
    setPersonalized(prev => !prev);
    setPage(1); // 重置页码
  }, []);
  
  // 处理结果反馈
  const handleResultFeedback = useCallback(async (resultId, action) => {
    if (!currentUser) {
      // 未登录用户不能提交反馈
      return { success: false, message: '请先登录后再提交反馈' };
    }
    
    try {
      await submitResultFeedback(resultId, action);
      return { success: true };
    } catch (err) {
      logError(err, 'ResultFeedback');
      return { success: false, message: '提交反馈失败，请稍后再试' };
    }
  }, [currentUser]);
  
  // 处理相关查询点击
  const handleRelatedQueryClick = useCallback((relatedQuery) => {
    handleSearch(relatedQuery);
  }, [handleSearch]);
  
  return {
    // 状态
    query,
    page,
    searchType,
    filters,
    results,
    totalResults,
    totalPages,
    searchTime,
    loading,
    error,
    relatedQueries,
    personalized,
    
    // 方法
    setQuery,
    setPage,
    setSearchType,
    setFilters,
    executeSearch,
    handleSearch,
    handlePageChange,
    handleFilterChange,
    handleTypeChange,
    handlePersonalizedToggle,
    handleResultFeedback,
    handleRelatedQueryClick
  };
};

export default useSearch;