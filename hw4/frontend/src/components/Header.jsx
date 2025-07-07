import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import './Header.css';

const Header = () => {
  const { currentUser, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="container header-container">
        <div className="logo">
          <Link to="/">NKU搜索</Link>
        </div>
        
        <nav className="nav">
          <ul className="nav-list">
            <li className="nav-item">
              <Link to="/" className="nav-link">首页</Link>
            </li>
            <li className="nav-item">
              <Link to="/documents" className="nav-link">文档搜索</Link>
            </li>
          </ul>
        </nav>
        
        <div className="user-actions">
          {currentUser ? (
            <div className="user-menu">
              <span className="username">{currentUser.username}</span>
              <div className="dropdown-menu">
                <Link to="/profile" className="dropdown-item">个人资料</Link>
                <button onClick={handleLogout} className="dropdown-item">退出登录</button>
              </div>
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-secondary">登录</Link>
              <Link to="/register" className="btn btn-primary">注册</Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;