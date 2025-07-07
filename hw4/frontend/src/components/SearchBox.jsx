import React, { useState, useEffect, useRef, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { getSearchSuggestions } from '../services/searchService';
import { getSearchHistory } from '../services/historyService';
import { parseSearchQuery } from '../services/searchService';
import { SEARCH_CONFIG } from '../config';
import './SearchBox.css';

const SearchBox = ({ initialQuery = '', onSearch, size = 'large', autoFocus = true }) => {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [history, setHistory] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const navigate = useNavigate();
  const { currentUser } = useContext(AuthContext);

  // 加载搜索历史
  useEffect(() => {
    const loadHistory = async () => {
      if (currentUser) {
        try {
          const historyData = await getSearchHistory(1, SEARCH_CONFIG.HISTORY_LIMIT);
          setHistory(historyData.items || []);
        } catch (err) {
          console.error('Failed to load search history:', err);
        }
      }
    };

    loadHistory();
  }, [currentUser]);

  // 自动聚焦
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  // 点击外部关闭建议框
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) && 
          inputRef.current && !inputRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 处理输入变化
  const handleInputChange = async (e) => {
    const value = e.target.value;
    setQuery(value);
    setError(null);

    if (value.trim() === '') {
      // 当输入为空时，显示历史记录
      setSuggestions([]);
      setShowSuggestions(true);
      return;
    }

    try {
      setLoading(true);
      const suggestionsData = await getSearchSuggestions(value, SEARCH_CONFIG.SUGGESTION_LIMIT);
      setSuggestions(suggestionsData || []);
      setShowSuggestions(true);
    } catch (err) {
      console.error('Failed to get search suggestions:', err);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索提交
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setShowSuggestions(false);
    
    // 解析搜索查询
    const parsedQuery = parseSearchQuery(query);
    
    if (onSearch) {
      // 如果提供了onSearch回调，则调用它
      onSearch(parsedQuery.query, parsedQuery);
    } else {
      // 否则导航到搜索结果页面
      if (parsedQuery.isDocumentSearch) {
        navigate(`/documents?q=${encodeURIComponent(parsedQuery.query)}&docType=${parsedQuery.docType.join(',')}`);
      } else {
        navigate(`/search?q=${encodeURIComponent(parsedQuery.query)}&type=${parsedQuery.searchType}`);
      }
    }
  };

  // 处理建议点击
  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    
    // 解析搜索查询
    const parsedQuery = parseSearchQuery(suggestion);
    
    if (onSearch) {
      onSearch(parsedQuery.query, parsedQuery);
    } else {
      if (parsedQuery.isDocumentSearch) {
        navigate(`/documents?q=${encodeURIComponent(parsedQuery.query)}&docType=${parsedQuery.docType.join(',')}`);
      } else {
        navigate(`/search?q=${encodeURIComponent(parsedQuery.query)}&type=${parsedQuery.searchType}`);
      }
    }
  };

  // 处理历史记录点击
  const handleHistoryClick = (historyItem) => {
    setQuery(historyItem.query);
    setShowSuggestions(false);
    
    // 解析搜索查询
    const parsedQuery = parseSearchQuery(historyItem.query);
    
    if (onSearch) {
      onSearch(parsedQuery.query, parsedQuery);
    } else {
      if (parsedQuery.isDocumentSearch) {
        navigate(`/documents?q=${encodeURIComponent(parsedQuery.query)}&docType=${parsedQuery.docType.join(',')}`);
      } else {
        navigate(`/search?q=${encodeURIComponent(parsedQuery.query)}&type=${parsedQuery.searchType}`);
      }
    }
  };

  // 处理输入框聚焦
  const handleFocus = () => {
    if (query.trim() === '') {
      // 当输入为空时，显示历史记录
      setShowSuggestions(true);
    } else if (suggestions.length > 0) {
      // 当有建议时，显示建议
      setShowSuggestions(true);
    }
  };

  return (
    <div className={`search-box ${size}`}>
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-container">
          <input
            type="text"
            className="search-input"
            placeholder="输入搜索关键词..."
            value={query}
            onChange={handleInputChange}
            onFocus={handleFocus}
            ref={inputRef}
            aria-label="搜索输入框"
          />
          {query && (
            <button 
              type="button" 
              className="clear-button"
              onClick={() => setQuery('')}
              aria-label="清除搜索"
            >
              ×
            </button>
          )}
        </div>
        <button type="submit" className="search-button" aria-label="搜索">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
          </svg>
        </button>
      </form>

      {showSuggestions && (
        <div className="suggestions-container" ref={suggestionsRef}>
          {loading && <div className="suggestions-loading">加载中...</div>}
          
          {error && <div className="suggestions-error">{error}</div>}
          
          {!loading && !error && query.trim() === '' && history.length > 0 && (
            <div className="history-list">
              <div className="suggestions-header">搜索历史</div>
              <ul>
                {history.map((item) => (
                  <li key={item.id} onClick={() => handleHistoryClick(item)}>
                    <span className="history-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
                        <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
                      </svg>
                    </span>
                    {item.query}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {!loading && !error && query.trim() !== '' && suggestions.length > 0 && (
            <div className="suggestions-list">
              <div className="suggestions-header">搜索建议</div>
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li key={index} onClick={() => handleSuggestionClick(suggestion)}>
                    <span className="suggestion-icon">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                      </svg>
                    </span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {!loading && !error && query.trim() !== '' && suggestions.length === 0 && (
            <div className="no-suggestions">没有找到相关建议</div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBox;