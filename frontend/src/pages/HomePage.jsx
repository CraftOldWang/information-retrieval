import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import SearchBox from '../components/SearchBox';
import { AuthContext } from '../contexts/AuthContext';
import './HomePage.css';

const HomePage = () => {
  const { currentUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSearch = (query, parsedQuery) => {
    if (parsedQuery.isDocumentSearch) {
      navigate(`/documents?q=${encodeURIComponent(query)}&docType=${parsedQuery.docType.join(',')}`);
    } else {
      navigate(`/search?q=${encodeURIComponent(query)}&type=${parsedQuery.searchType}`);
    }
  };

  return (
    <div className="home-page">
      <Header />
      
      <main className="home-content">
        <div className="search-container">
          <div className="logo-container">
            <h1 className="logo-text">NKU<span className="logo-highlight">搜索</span></h1>
          </div>
          
          <SearchBox 
            onSearch={handleSearch} 
            size="large" 
            autoFocus={true} 
          />
          
          <div className="search-tips">
            <p>搜索提示：</p>
            <ul>
              <li>使用引号 "" 进行短语搜索</li>
              <li>使用 filetype:pdf 搜索特定类型的文档</li>
              <li>使用 * 和 ? 进行通配符搜索</li>
            </ul>
          </div>
        </div>
        
        {currentUser && (
          <div className="personalized-section">
            <h2>个性化推荐</h2>
            <p>欢迎回来，{currentUser.username}！这里是您可能感兴趣的内容。</p>
            {/* 这里可以添加个性化推荐内容 */}
          </div>
        )}
      </main>
      
      <Footer />
    </div>
  );
};

export default HomePage;