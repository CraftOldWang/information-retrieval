import React, { useState, useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { AuthContext } from '../contexts/AuthContext';
import './AuthPages.css';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { register, currentUser, error: authError } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // 如果用户已登录，重定向到首页
  useEffect(() => {
    if (currentUser) {
      navigate('/');
    }
  }, [currentUser, navigate]);

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
    
    // 清除通用错误
    if (errors.general) {
      setErrors(prev => ({
        ...prev,
        general: ''
      }));
    }
  };

  // 表单验证
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    } else if (formData.username.length < 3) {
      newErrors.username = '用户名至少需要3个字符';
    }
    
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码至少需要6个字符';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
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
      // 创建符合后端要求的用户数据对象
      const userData = {
        username: formData.username,
        password: formData.password
        // 可以添加其他可选字段如college, major, grade
      };
      
      await register(userData);
      // 注册成功后的重定向在useEffect中处理
    } catch (err) {
      console.error('注册失败:', err);
      // 设置具体的错误信息
      if (err.message.includes('Username already exists')) {
        setErrors(prev => ({
          ...prev,
          username: '用户名已存在'
        }));
      } else {
        // 显示通用错误
        setErrors(prev => ({
          ...prev,
          general: err.message || '注册失败，请稍后重试'
        }));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <Header />
      
      <main className="auth-content">
        <div className="auth-container">
          <h1 className="auth-title">注册</h1>
          
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
            
            <div className="form-group">
              <label htmlFor="confirmPassword">确认密码</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                disabled={isSubmitting}
              />
              {errors.confirmPassword && <div className="error-message">{errors.confirmPassword}</div>}
              
              {/* 显示通用错误信息 */}
              {errors.general && <div className="error-message auth-error">{errors.general}</div>}
              
              {authError && <div className="error-message auth-error">{authError}</div>}
            </div>
            
            <button 
              type="submit" 
              className="auth-button" 
              disabled={isSubmitting}
            >
              {isSubmitting ? '注册中...' : '注册'}
            </button>
          </form>
          
          <div className="auth-links">
            <p>已有账号？<Link to="/login">立即登录</Link></p>
          </div>
        </div>
      </main>
      
       
    </div>
  );
};

export default RegisterPage;