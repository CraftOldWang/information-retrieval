import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import './SearchResult.css';

const SearchResult = ({ result, onFeedback }) => {
  const { currentUser } = useContext(AuthContext);
  
  // 格式化日期
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  // 处理反馈点击
  const handleFeedbackClick = (feedbackType) => {
    if (onFeedback && currentUser) {
      onFeedback(result.id, feedbackType);
    }
  };

  // 截断长文本
  const truncateText = (text, maxLength = 200) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // 高亮匹配的文本
  const highlightText = (text, highlights) => {
    if (!highlights || !highlights.length || !text) return text;
    
    let result = text;
    highlights.forEach(highlight => {
      const regex = new RegExp(highlight, 'gi');
      result = result.replace(regex, match => `<mark>${match}</mark>`);
    });
    
    return <span dangerouslySetInnerHTML={{ __html: result }} />;
  };

  return (
    <div className="search-result">
      <div className="result-header">
        {result.favicon && (
          <img src={result.favicon} alt="" className="result-favicon" />
        )}
        <a href={result.url} className="result-url" target="_blank" rel="noopener noreferrer">
          {result.domain || result.url}
        </a>
        {result.date && (
          <span className="result-date">{formatDate(result.date)}</span>
        )}
      </div>
      
      <h3 className="result-title">
        <a href={result.url} target="_blank" rel="noopener noreferrer">
          {highlightText(result.title, result.highlights?.title)}
        </a>
      </h3>
      
      <div className="result-snippet">
        {highlightText(truncateText(result.snippet || result.content), result.highlights?.content)}
      </div>
      
      <div className="result-actions">
        <Link to={`/snapshot/${result.id}`} className="result-action">
          <span className="action-icon">📄</span> 网页快照
        </Link>
        
        {currentUser && (
          <div className="result-feedback">
            <button 
              className="feedback-button" 
              onClick={() => handleFeedbackClick('like')}
              aria-label="喜欢"
            >
              <span className="feedback-icon">👍</span>
            </button>
            <button 
              className="feedback-button" 
              onClick={() => handleFeedbackClick('dislike')}
              aria-label="不喜欢"
            >
              <span className="feedback-icon">👎</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchResult;