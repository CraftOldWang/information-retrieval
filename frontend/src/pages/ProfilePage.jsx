import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { AuthContext } from '../contexts/AuthContext';
import './ProfilePage.css';

const ProfilePage = () => {
  const { currentUser, updateProfile, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const [profileData, setProfileData] = useState({
    username: '',
    email: '',
    interests: '',
    notification: false
  });
  
  const [searchHistory, setSearchHistory] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  
  // 如果用户未登录，重定向到登录页面
  useEffect(() => {
    if (!currentUser) {
      navigate('/login', { state: { from: { pathname: '/profile' } } });
    } else {
      loadUserProfile();
      loadSearchHistory();
    }
  }, [currentUser, navigate]);
  
  // 加载用户资料
  const loadUserProfile = async () => {
    setIsLoading(true);
    try {
      // 这里应该是从API获取用户资料的逻辑
      // 模拟API调用
      setTimeout(() => {
        setProfileData({
          username: currentUser.username || '',
          email: currentUser.email || '',
          interests: currentUser.interests || '',
          notification: currentUser.notification || false
        });
        setIsLoading(false);
      }, 500);
    } catch (err) {
      console.error('加载用户资料失败:', err);
      setError('加载用户资料失败，请稍后再试');
      setIsLoading(false);
    }
  };
  
  // 加载搜索历史
  const loadSearchHistory = async () => {
    try {
      // 这里应该是从API获取搜索历史的逻辑
      // 模拟API调用
      setTimeout(() => {
        setSearchHistory([
          { id: 1, query: '信息检索系统', timestamp: new Date(Date.now() - 86400000).toISOString() },
          { id: 2, query: '向量空间模型', timestamp: new Date(Date.now() - 172800000).toISOString() },
          { id: 3, query: 'TF-IDF算法', timestamp: new Date(Date.now() - 259200000).toISOString() },
          { id: 4, query: '搜索引擎优化', timestamp: new Date(Date.now() - 345600000).toISOString() },
          { id: 5, query: '自然语言处理', timestamp: new Date(Date.now() - 432000000).toISOString() }
        ]);
      }, 500);
    } catch (err) {
      console.error('加载搜索历史失败:', err);
      // 不显示错误，只是不显示历史记录
    }
  };
  
  // 处理表单输入变化
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // 这里应该是更新用户资料的API调用
      await updateProfile(profileData);
      setSuccessMessage('个人资料已成功更新');
      setIsEditing(false);
      
      // 3秒后清除成功消息
      setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
    } catch (err) {
      console.error('更新个人资料失败:', err);
      setError('更新个人资料失败，请稍后再试');
    }
  };
  
  // 处理删除搜索历史
  const handleDeleteHistory = async (id) => {
    try {
      // 这里应该是删除搜索历史的API调用
      // 模拟API调用
      setSearchHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error('删除搜索历史失败:', err);
    }
  };
  
  // 处理清空所有搜索历史
  const handleClearAllHistory = async () => {
    try {
      // 这里应该是清空所有搜索历史的API调用
      // 模拟API调用
      setSearchHistory([]);
    } catch (err) {
      console.error('清空搜索历史失败:', err);
    }
  };
  
  // 格式化日期
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // 处理注销
  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (isLoading) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-content">
          <div className="loading-indicator">加载中...</div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="profile-page">
      <Header />
      
      <main className="profile-content">
        <div className="profile-container">
          <h1 className="profile-title">个人资料</h1>
          
          {error && <div className="error-message">{error}</div>}
          {successMessage && <div className="success-message">{successMessage}</div>}
          
          <div className="profile-card">
            <div className="profile-header">
              <div className="profile-avatar">
                {profileData.username.charAt(0).toUpperCase()}
              </div>
              <div className="profile-info">
                <h2>{profileData.username}</h2>
                <p>{profileData.email}</p>
              </div>
              <button 
                className="edit-button"
                onClick={() => setIsEditing(!isEditing)}
              >
                {isEditing ? '取消' : '编辑'}
              </button>
            </div>
            
            {isEditing ? (
              <form className="profile-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="username">用户名</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={profileData.username}
                    onChange={handleChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">邮箱</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={profileData.email}
                    onChange={handleChange}
                    disabled
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="interests">兴趣标签（用逗号分隔）</label>
                  <input
                    type="text"
                    id="interests"
                    name="interests"
                    value={profileData.interests}
                    onChange={handleChange}
                    placeholder="例如：人工智能,机器学习,数据挖掘"
                  />
                </div>
                
                <div className="form-group checkbox-group">
                  <input
                    type="checkbox"
                    id="notification"
                    name="notification"
                    checked={profileData.notification}
                    onChange={handleChange}
                  />
                  <label htmlFor="notification">接收搜索推荐通知</label>
                </div>
                
                <button type="submit" className="save-button">保存更改</button>
              </form>
            ) : (
              <div className="profile-details">
                <div className="detail-item">
                  <span className="detail-label">兴趣标签</span>
                  <div className="interest-tags">
                    {profileData.interests ? 
                      profileData.interests.split(',').map((tag, index) => (
                        <span key={index} className="interest-tag">{tag.trim()}</span>
                      )) : 
                      <span className="no-data">未设置</span>
                    }
                  </div>
                </div>
                
                <div className="detail-item">
                  <span className="detail-label">通知设置</span>
                  <span>{profileData.notification ? '已开启' : '已关闭'}</span>
                </div>
              </div>
            )}
          </div>
          
          <div className="search-history-section">
            <div className="section-header">
              <h2>搜索历史</h2>
              {searchHistory.length > 0 && (
                <button 
                  className="clear-all-button"
                  onClick={handleClearAllHistory}
                >
                  清空全部
                </button>
              )}
            </div>
            
            {searchHistory.length > 0 ? (
              <ul className="search-history-list">
                {searchHistory.map(item => (
                  <li key={item.id} className="history-item">
                    <div className="history-content">
                      <span className="history-query">{item.query}</span>
                      <span className="history-time">{formatDate(item.timestamp)}</span>
                    </div>
                    <button 
                      className="delete-button"
                      onClick={() => handleDeleteHistory(item.id)}
                      aria-label="删除"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="no-history">暂无搜索历史</div>
            )}
          </div>
          
          <div className="account-actions">
            <button className="logout-button" onClick={handleLogout}>
              退出登录
            </button>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default ProfilePage;