import React, { useState, useContext, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { AuthContext } from '../contexts/AuthContext';
import './AuthPages.css';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login, currentUser, error: authError } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  // 如果用户已登录，重定向到首页或来源页面
  useEffect(() => {
    if (currentUser) {
      const from = location.state?.from?.pathname || '/';
      navigate(from);
    }
  }, [currentUser, navigate, location]);

  // 处理表单输入变化
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // 表单验证
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    }
    
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    try {
      await login(formData.username, formData.password);
      // 登录成功后的重定向在useEffect中处理
    } catch (err) {
      console.error('登录失败:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <Header />
      
      <main className="auth-content">
        <div className="auth-container">
          <h1 className="auth-title">登录</h1>
          
          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                disabled={isSubmitting}
                autoFocus
              />
              {errors.username && <div className="error-message">{errors.username}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="password">密码</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                disabled={isSubmitting}
              />
              {errors.password && <div className="error-message">{errors.password}</div>}
            </div>
            
            {authError && <div className="error-message auth-error">{authError}</div>}
            
            <button 
              type="submit" 
              className="auth-button" 
              disabled={isSubmitting}
            >
              {isSubmitting ? '登录中...' : '登录'}
            </button>
          </form>
          
          <div className="auth-links">
            <p>还没有账号？<Link to="/register">立即注册</Link></p>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default LoginPage;