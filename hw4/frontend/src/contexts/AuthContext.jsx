import React, { createContext, useState, useEffect } from 'react';
import { loginUser, registerUser, getUserProfile } from '../services/authService';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 检查本地存储中是否有令牌
    const token = localStorage.getItem('token');
    if (token) {
      // 获取用户资料
      getUserProfile()
        .then(userData => {
          setCurrentUser(userData);
          setLoading(false);
        })
        .catch(err => {
          console.error('获取用户资料失败:', err);
          localStorage.removeItem('token'); // 令牌无效，清除
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // 登录函数
  const login = async (username, password) => {
    try {
      setError(null);
      const data = await loginUser(username, password);
      localStorage.setItem('token', data.access_token);
      setCurrentUser(data.user);
      return data.user;
    } catch (err) {
      setError(err.message || '登录失败');
      throw err;
    }
  };

  // 注册函数
  const register = async (userData) => {
    try {
      setError(null);
      const data = await registerUser(userData);
      localStorage.setItem('token', data.access_token);
      setCurrentUser(data.user);
      return data.user;
    } catch (err) {
      setError(err.message || '注册失败');
      throw err;
    }
  };

  // 登出函数
  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};