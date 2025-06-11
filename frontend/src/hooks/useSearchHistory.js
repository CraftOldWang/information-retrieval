import { useState, useEffect, useCallback, useContext } from 'react';
import { getSearchHistory, deleteSearchHistory, clearSearchHistory } from '../services/searchService';
import { normalizeError, logError } from '../utils/errorHandler';
import { AuthContext } from '../contexts/AuthContext';
import { SEARCH_CONFIG } from '../config';

/**
 * 搜索历史钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 搜索历史状态和方法
 */
const useSearchHistory = (options = {}) => {
  const {
    limit = SEARCH_CONFIG.HISTORY_LIMIT,
    autoLoad = true
  } = options;
  
  const { currentUser } = useContext(AuthContext);
  
  // 状态
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);
  
  // 加载搜索历史
  const loadHistory = useCallback(async () => {
    if (!currentUser) {
      setHistory([]);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getSearchHistory(limit);
      setHistory(response.history || []);
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'SearchHistory');
    } finally {
      setLoading(false);
    }
  }, [currentUser, limit]);
  
  // 删除单条搜索历史
  const deleteHistoryItem = useCallback(async (historyId) => {
    if (!currentUser) {
      return { success: false, message: '用户未登录' };
    }
    
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    
    try {
      await deleteSearchHistory(historyId);
      
      // 更新本地历史列表
      setHistory(prev => prev.filter(item => item.id !== historyId));
      
      setActionSuccess('搜索记录已删除');
      
      // 3秒后清除成功状态
      setTimeout(() => {
        setActionSuccess(null);
      }, 3000);
      
      return { success: true, message: '搜索记录已删除' };
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'DeleteSearchHistory');
      return { success: false, message: normalizedError.message || '删除搜索记录失败' };
    } finally {
      setLoading(false);
    }
  }, [currentUser]);
  
  // 清空所有搜索历史
  const clearAllHistory = useCallback(async () => {
    if (!currentUser) {
      return { success: false, message: '用户未登录' };
    }
    
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    
    try {
      await clearSearchHistory();
      
      // 清空本地历史列表
      setHistory([]);
      
      setActionSuccess('所有搜索记录已清空');
      
      // 3秒后清除成功状态
      setTimeout(() => {
        setActionSuccess(null);
      }, 3000);
      
      return { success: true, message: '所有搜索记录已清空' };
    } catch (err) {
      const normalizedError = normalizeError(err);
      setError(normalizedError);
      logError(err, 'ClearSearchHistory');
      return { success: false, message: normalizedError.message || '清空搜索记录失败' };
    } finally {
      setLoading(false);
    }
  }, [currentUser]);
  
  // 当用户登录状态变化时加载历史
  useEffect(() => {
    if (autoLoad) {
      loadHistory();
    }
  }, [currentUser, autoLoad, loadHistory]);
  
  return {
    // 状态
    history,
    loading,
    error,
    actionSuccess,
    
    // 方法
    loadHistory,
    deleteHistoryItem,
    clearAllHistory
  };
};

export default useSearchHistory;