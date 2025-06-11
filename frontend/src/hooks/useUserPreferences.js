import { useState, useEffect, useCallback, useContext } from 'react';
import { getUserPreferences, updateUserPreferences } from '../services/authService';
import { normalizeError, logError } from '../utils/errorHandler';
import { AuthContext } from '../contexts/AuthContext';

/**
 * 用户偏好设置钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 用户偏好状态和方法
 */
const useUserPreferences = (options = {}) => {
  const {
    autoLoad = true
  } = options;
  
  const { currentUser } = useContext(AuthContext);
  
  // 默认偏好设置
  const defaultPreferences = {
    theme: 'system',
    searchResultsPerPage: 10,
    enablePersonalizedSearch: true,
    enableSearchHistory: true,
    enableNotifications: true,
    interests: [],
    preferredLanguages: ['zh-CN'],
    preferredDocTypes: []
  };
  
  // 状态
  const [preferences, setPreferences] = useState(defaultPreferences);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // 加载用户偏好设置
  const loadPreferences = useCallback(async () => {
    if (!currentUser) {
      setPreferences(defaultPreferences);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUserPreferences();
      setPreferences({
        ...defaultPreferences,
        ...response
      });
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'UserPreferences');
    } finally {
      setLoading(false);
    }
  }, [currentUser]);
  
  // 保存用户偏好设置
  const savePreferences = useCallback(async (newPreferences) => {
    if (!currentUser) {
      return { success: false, message: '用户未登录' };
    }
    
    setLoading(true);
    setError(null);
    setSaveSuccess(false);
    
    try {
      // 合并当前偏好和新偏好
      const updatedPreferences = {
        ...preferences,
        ...newPreferences
      };
      
      await updateUserPreferences(updatedPreferences);
      
      setPreferences(updatedPreferences);
      setSaveSuccess(true);
      
      // 3秒后清除成功状态
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
      
      return { success: true, message: '偏好设置已保存' };
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'SaveUserPreferences');
      return { success: false, message: normalizedError.message || '保存偏好设置失败' };
    } finally {
      setLoading(false);
    }
  }, [currentUser, preferences]);
  
  // 更新单个偏好设置
  const updatePreference = useCallback((key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);
  
  // 重置偏好设置
  const resetPreferences = useCallback(() => {
    setPreferences(defaultPreferences);
  }, []);
  
  // 当用户登录状态变化时加载偏好设置
  useEffect(() => {
    if (autoLoad) {
      loadPreferences();
    }
  }, [currentUser, autoLoad, loadPreferences]);
  
  return {
    // 状态
    preferences,
    loading,
    error,
    saveSuccess,
    
    // 方法
    loadPreferences,
    savePreferences,
    updatePreference,
    resetPreferences
  };
};

export default useUserPreferences;