import React, { useState, useEffect, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import SearchBox from '../components/SearchBox';
import SearchResult from '../components/SearchResult';
import { AuthContext } from '../contexts/AuthContext';
import { search, personalizedSearch, /* getRelatedQueries */ } from '../services/searchService';
import { submitFeedback } from '../services/authService';
import { SEARCH_TYPES } from '../config';
import './SearchResultsPage.css';

const SearchResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  
  // 从URL获取查询参数
  const queryParams = new URLSearchParams(location.search);
  const initialQuery = queryParams.get('q') || '';
  const initialType = queryParams.get('type') || 'normal';
  const initialPage = parseInt(queryParams.get('page') || '1', 10);
  
  // 状态管理
  const [query, setQuery] = useState(initialQuery);
  const [searchType, setSearchType] = useState(initialType);
  const [results, setResults] = useState([]);
  const [relatedQueries, setRelatedQueries] = useState([]);
  const [pagination, setPagination] = useState({
    page: initialPage,
    pageSize: 10,
    totalPages: 1,
    totalResults: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    domain: queryParams.get('domain') || '',
    dateFrom: queryParams.get('dateFrom') || '',
    dateTo: queryParams.get('dateTo') || ''
  });

  // 执行搜索
  const performSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // 根据用户是否登录选择搜索方法
      const searchMethod = currentUser && queryParams.get('personalized') === 'true' 
        ? personalizedSearch 
        : search;
      
      const response = await searchMethod(
        query, 
        pagination.page, 
        pagination.pageSize, 
        searchType,
        filters
      );
      
      setResults(response.results || []);
      setPagination({
        page: response.page || 1,
        pageSize: response.page_size || 10,
        totalPages: response.total_pages || 1,
        totalResults: response.total_results || 0
      });
      
      // 获取相关查询 - 暂时注释掉避免404错误
      // if (query.trim()) {
      //   const relatedData = await getRelatedQueries(query);
      //   setRelatedQueries(relatedData || []);
      // }
      setRelatedQueries([]); // 暂时设置为空数组
    } catch (err) {
      setError(err.message || '搜索时发生错误');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // 当URL参数变化时执行搜索
  useEffect(() => {
    setQuery(initialQuery);
    setSearchType(initialType);
    setPagination(prev => ({ ...prev, page: initialPage }));
    setFilters({
      domain: queryParams.get('domain') || '',
      dateFrom: queryParams.get('dateFrom') || '',
      dateTo: queryParams.get('dateTo') || ''
    });
    
    if (initialQuery.trim()) {
      performSearch();
    }
  }, [location.search]);

  // 处理搜索提交
  const handleSearch = (newQuery, parsedQuery) => {
    if (!newQuery.trim()) return;
    
    const params = new URLSearchParams();
    params.set('q', newQuery);
    params.set('type', parsedQuery.searchType || 'normal');
    params.set('page', '1');
    
    // 添加过滤器参数
    if (filters.domain) params.set('domain', filters.domain);
    if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
    if (filters.dateTo) params.set('dateTo', filters.dateTo);
    
    // 如果用户已登录且选择了个性化搜索
    if (currentUser && queryParams.get('personalized') === 'true') {
      params.set('personalized', 'true');
    }
    
    navigate(`/search?${params.toString()}`);
  };

  // 处理页码变化
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.totalPages) return;
    
    const params = new URLSearchParams(location.search);
    params.set('page', newPage.toString());
    navigate(`/search?${params.toString()}`);
  };

  // 处理搜索类型变化
  const handleSearchTypeChange = (newType) => {
    const params = new URLSearchParams(location.search);
    params.set('type', newType);
    params.set('page', '1');
    navigate(`/search?${params.toString()}`);
  };

  // 处理过滤器变化
  const handleFilterChange = (newFilters) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    
    const params = new URLSearchParams(location.search);
    params.set('page', '1');
    
    // 更新过滤器参数
    Object.entries(updatedFilters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });
    
    navigate(`/search?${params.toString()}`);
  };

  // 处理反馈提交
  const handleFeedback = async (resultId, feedbackType) => {
    if (!currentUser) return;
    
    try {
      await submitFeedback({
        query_id: query,
        result_id: resultId,
        feedback_type: feedbackType
      });
    } catch (err) {
      console.error('提交反馈失败:', err);
    }
  };

  // 处理相关查询点击
  const handleRelatedQueryClick = (relatedQuery) => {
    const params = new URLSearchParams();
    params.set('q', relatedQuery);
    params.set('type', 'normal');
    params.set('page', '1');
    navigate(`/search?${params.toString()}`);
  };

  // 切换个性化搜索
  const togglePersonalizedSearch = () => {
    if (!currentUser) return;
    
    const params = new URLSearchParams(location.search);
    const isPersonalized = params.get('personalized') === 'true';
    
    if (isPersonalized) {
      params.delete('personalized');
    } else {
      params.set('personalized', 'true');
    }
    
    navigate(`/search?${params.toString()}`);
  };

  return (
    <div className="search-results-page">
      <Header />
      
      <main className="search-results-content">
        <div className="search-header">
          <div className="search-box-container">
            <SearchBox 
              initialQuery={query} 
              onSearch={handleSearch} 
              size="medium" 
              autoFocus={false} 
            />
          </div>
          
          <div className="search-options">
            <div className="search-types">
              {SEARCH_TYPES.map(type => (
                <button 
                  key={type.value}
                  className={`search-type-button ${searchType === type.value ? 'active' : ''}`}
                  onClick={() => handleSearchTypeChange(type.value)}
                >
                  {type.label}
                </button>
              ))}
            </div>
            
            {currentUser && (
              <button 
                className={`personalized-button ${queryParams.get('personalized') === 'true' ? 'active' : ''}`}
                onClick={togglePersonalizedSearch}
              >
                个性化搜索
              </button>
            )}
          </div>
          
          <div className="search-filters">
            <div className="filter-group">
              <label htmlFor="domain-filter">域名:</label>
              <input 
                id="domain-filter"
                type="text" 
                value={filters.domain} 
                onChange={(e) => handleFilterChange({ domain: e.target.value })}
                placeholder="例如: nku.edu.cn"
              />
            </div>
            
            <div className="filter-group">
              <label>日期范围:</label>
              <input 
                type="date" 
                value={filters.dateFrom} 
                onChange={(e) => handleFilterChange({ dateFrom: e.target.value })}
              />
              <span>至</span>
              <input 
                type="date" 
                value={filters.dateTo} 
                onChange={(e) => handleFilterChange({ dateTo: e.target.value })}
              />
            </div>
          </div>
        </div>
        
        <div className="search-results-container">
          {loading ? (
            <div className="loading-indicator">正在搜索...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : results.length > 0 ? (
            <>
              <div className="results-info">
                找到约 {pagination.totalResults} 条结果 (用时 {results[0]?.search_time || 0} 秒)
              </div>
              
              <div className="results-list">
                {results.map(result => (
                  <SearchResult 
                    key={result.id} 
                    result={result} 
                    onFeedback={handleFeedback} 
                  />
                ))}
              </div>
              
              <div className="pagination">
                <button 
                  className="pagination-button"
                  disabled={pagination.page <= 1}
                  onClick={() => handlePageChange(pagination.page - 1)}
                >
                  上一页
                </button>
                
                <span className="pagination-info">
                  第 {pagination.page} 页，共 {pagination.totalPages} 页
                </span>
                
                <button 
                  className="pagination-button"
                  disabled={pagination.page >= pagination.totalPages}
                  onClick={() => handlePageChange(pagination.page + 1)}
                >
                  下一页
                </button>
              </div>
            </>
          ) : query ? (
            <div className="no-results">没有找到与 "{query}" 相关的结果</div>
          ) : null}
          
          {relatedQueries.length > 0 && (
            <div className="related-queries">
              <h3>相关搜索</h3>
              <ul>
                {relatedQueries.map((relatedQuery, index) => (
                  <li key={index}>
                    <button onClick={() => handleRelatedQueryClick(relatedQuery)}>
                      {relatedQuery}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
      
       
    </div>
  );
};

export default SearchResultsPage;