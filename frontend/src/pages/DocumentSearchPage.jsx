import React, { useState, useEffect, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import SearchBox from '../components/SearchBox';
import SearchResult from '../components/SearchResult';
import { AuthContext } from '../contexts/AuthContext';
import { searchDocuments } from '../services/searchService';
import { submitFeedback } from '../services/authService';
import { DOCUMENT_TYPES } from '../config';
import './DocumentSearchPage.css';

const DocumentSearchPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);
  
  // 从URL获取查询参数
  const queryParams = new URLSearchParams(location.search);
  const initialQuery = queryParams.get('q') || '';
  const initialDocTypes = queryParams.get('docType') ? queryParams.get('docType').split(',') : [];
  const initialPage = parseInt(queryParams.get('page') || '1', 10);
  
  // 状态管理
  const [query, setQuery] = useState(initialQuery);
  const [docTypes, setDocTypes] = useState(initialDocTypes);
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState({
    page: initialPage,
    pageSize: 10,
    totalPages: 1,
    totalResults: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    dateFrom: queryParams.get('dateFrom') || '',
    dateTo: queryParams.get('dateTo') || ''
  });

  // 执行搜索
  const performSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await searchDocuments(
        query, 
        pagination.page, 
        pagination.pageSize, 
        docTypes,
        filters
      );
      
      setResults(response.results || []);
      setPagination({
        page: response.page || 1,
        pageSize: response.page_size || 10,
        totalPages: response.total_pages || 1,
        totalResults: response.total_results || 0
      });
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
    setDocTypes(initialDocTypes);
    setPagination(prev => ({ ...prev, page: initialPage }));
    setFilters({
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
    params.set('page', '1');
    
    // 如果解析的查询包含文档类型，则使用它
    if (parsedQuery.isDocumentSearch && parsedQuery.docType) {
      params.set('docType', parsedQuery.docType.join(','));
    } else if (docTypes.length > 0) {
      // 否则使用当前选择的文档类型
      params.set('docType', docTypes.join(','));
    }
    
    // 添加过滤器参数
    if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
    if (filters.dateTo) params.set('dateTo', filters.dateTo);
    
    navigate(`/documents?${params.toString()}`);
  };

  // 处理页码变化
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.totalPages) return;
    
    const params = new URLSearchParams(location.search);
    params.set('page', newPage.toString());
    navigate(`/documents?${params.toString()}`);
  };

  // 处理文档类型变化
  const handleDocTypeChange = (type, checked) => {
    let newDocTypes;
    if (checked) {
      newDocTypes = [...docTypes, type];
    } else {
      newDocTypes = docTypes.filter(t => t !== type);
    }
    
    setDocTypes(newDocTypes);
    
    const params = new URLSearchParams(location.search);
    params.set('page', '1');
    
    if (newDocTypes.length > 0) {
      params.set('docType', newDocTypes.join(','));
    } else {
      params.delete('docType');
    }
    
    navigate(`/documents?${params.toString()}`);
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
    
    navigate(`/documents?${params.toString()}`);
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

  return (
    <div className="document-search-page">
      <Header />
      
      <main className="document-search-content">
        <div className="search-header">
          <div className="search-box-container">
            <SearchBox 
              initialQuery={query} 
              onSearch={handleSearch} 
              size="medium" 
              autoFocus={false} 
            />
          </div>
          
          <div className="document-filters">
            <div className="doc-types">
              <h3>文档类型</h3>
              <div className="doc-type-options">
                {DOCUMENT_TYPES.map(type => (
                  <label key={type.value} className="doc-type-option">
                    <input 
                      type="checkbox" 
                      checked={docTypes.includes(type.value)} 
                      onChange={(e) => handleDocTypeChange(type.value, e.target.checked)} 
                    />
                    <span>{type.label}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div className="date-filter">
              <h3>日期范围</h3>
              <div className="date-inputs">
                <input 
                  type="date" 
                  value={filters.dateFrom} 
                  onChange={(e) => handleFilterChange({ dateFrom: e.target.value })}
                  aria-label="开始日期"
                />
                <span>至</span>
                <input 
                  type="date" 
                  value={filters.dateTo} 
                  onChange={(e) => handleFilterChange({ dateTo: e.target.value })}
                  aria-label="结束日期"
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="document-results-container">
          {loading ? (
            <div className="loading-indicator">正在搜索文档...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : results.length > 0 ? (
            <>
              <div className="results-info">
                找到约 {pagination.totalResults} 个文档 (用时 {results[0]?.search_time || 0} 秒)
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
            <div className="no-results">没有找到与 "{query}" 相关的文档</div>
          ) : (
            <div className="search-prompt">
              <p>请输入关键词搜索文档</p>
              <p className="search-tip">提示: 使用 filetype:pdf 可以直接搜索PDF文件</p>
            </div>
          )}
        </div>
      </main>
      
       
    </div>
  );
};

export default DocumentSearchPage;