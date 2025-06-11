import { useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { searchDocuments } from '../services/searchService';
import { parseSearchQuery, buildSearchFilters, extractSearchParams } from '../utils/searchUtils';
import { buildQueryString, parseQueryString } from '../utils/helpers';
import { normalizeError, logError } from '../utils/errorHandler';
import { AuthContext } from '../contexts/AuthContext';
import { SEARCH_CONFIG, DOC_TYPES } from '../config';

/**
 * 文档搜索钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 文档搜索状态和方法
 */
const useDocumentSearch = (options = {}) => {
  const {
    initialQuery = '',
    initialPage = 1,
    initialDocTypes = [],
    initialDateRange = { start: null, end: null },
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
  const [docTypes, setDocTypes] = useState(urlSearchParams.filters?.docType || initialDocTypes);
  const [dateRange, setDateRange] = useState({
    start: urlSearchParams.filters?.dateStart || initialDateRange.start,
    end: urlSearchParams.filters?.dateEnd || initialDateRange.end
  });
  const [results, setResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [personalized, setPersonalized] = useState(!!currentUser);
  
  // 执行文档搜索
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
      // 构建过滤器
      const filters = {
        docType: docTypes,
        dateStart: dateRange.start,
        dateEnd: dateRange.end
      };
      
      const searchParams = {
        page,
        pageSize: SEARCH_CONFIG.DEFAULT_PAGE_SIZE,
        personalized: personalized && !!currentUser,
        filters: buildSearchFilters(filters)
      };
      
      // 执行文档搜索
      const response = await searchDocuments(query, {
        ...searchParams,
        docType: docTypes
      });
      
      setResults(response.results || []);
      setTotalResults(response.total || 0);
      setTotalPages(response.total_pages || 0);
      setSearchTime(response.search_time || 0);
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'DocumentSearch');
    } finally {
      setLoading(false);
    }
  }, [query, page, docTypes, dateRange, personalized, currentUser]);
  
  // 当URL参数变化时更新状态
  useEffect(() => {
    if (location.search) {
      const urlParams = extractSearchParams(queryParams);
      
      if (urlParams.query !== query) setQuery(urlParams.query || '');
      if (urlParams.page !== page) setPage(urlParams.page || 1);
      
      // 更新文档类型过滤器
      if (urlParams.filters?.docType) {
        setDocTypes(urlParams.filters.docType);
      }
      
      // 更新日期范围过滤器
      if (urlParams.filters?.dateStart || urlParams.filters?.dateEnd) {
        setDateRange({
          start: urlParams.filters.dateStart || dateRange.start,
          end: urlParams.filters.dateEnd || dateRange.end
        });
      }
    }
  }, [location.search, queryParams]);
  
  // 自动执行搜索
  useEffect(() => {
    if (autoSearch && query) {
      executeSearch();
      
      // 更新URL
      const filters = {
        docType: docTypes.length > 0 ? docTypes : undefined,
        dateStart: dateRange.start,
        dateEnd: dateRange.end
      };
      
      const searchParams = {
        q: query,
        page: page > 1 ? page : undefined,
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
  }, [query, page, docTypes, dateRange, personalized, autoSearch, executeSearch, navigate, location.pathname, location.search]);
  
  // 处理搜索提交
  const handleSearch = useCallback((newQuery) => {
    if (newQuery === query) {
      // 如果查询没变，但页码不是1，重置页码并重新搜索
      if (page !== 1) {
        setPage(1);
      } else {
        // 否则直接重新搜索
        executeSearch();
      }
    } else {
      // 查询变化，重置页码并更新查询
      setQuery(newQuery);
      setPage(1);
    }
  }, [query, page, executeSearch]);
  
  // 处理页码变化
  const handlePageChange = useCallback((newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  }, [totalPages]);
  
  // 处理文档类型变化
  const handleDocTypeChange = useCallback((newDocTypes) => {
    setDocTypes(newDocTypes);
    setPage(1); // 重置页码
  }, []);
  
  // 处理日期范围变化
  const handleDateRangeChange = useCallback((newDateRange) => {
    setDateRange(newDateRange);
    setPage(1); // 重置页码
  }, []);
  
  // 处理个性化搜索切换
  const handlePersonalizedToggle = useCallback(() => {
    setPersonalized(prev => !prev);
    setPage(1); // 重置页码
  }, []);
  
  // 获取可用的文档类型
  const getAvailableDocTypes = useCallback(() => {
    return DOC_TYPES.map(type => ({
      id: type.id,
      name: type.name,
      icon: type.icon
    }));
  }, []);
  
  return {
    // 状态
    query,
    page,
    docTypes,
    dateRange,
    results,
    totalResults,
    totalPages,
    searchTime,
    loading,
    error,
    personalized,
    
    // 方法
    setQuery,
    setPage,
    setDocTypes,
    setDateRange,
    executeSearch,
    handleSearch,
    handlePageChange,
    handleDocTypeChange,
    handleDateRangeChange,
    handlePersonalizedToggle,
    getAvailableDocTypes
  };
};

export default useDocumentSearch;