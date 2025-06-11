import { useState, useEffect, useCallback } from 'react';

/**
 * 本地存储钩子
 * @param {string} key - 存储键名
 * @param {any} initialValue - 初始值
 * @returns {Array} - [storedValue, setValue, removeValue]
 */
const useLocalStorage = (key, initialValue) => {
  // 获取初始值的函数
  const readValue = useCallback(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);
  
  // 状态
  const [storedValue, setStoredValue] = useState(readValue);
  
  // 设置值的函数
  const setValue = useCallback((value) => {
    if (typeof window === 'undefined') {
      console.warn(`Tried setting localStorage key "${key}" even though environment is not a client`);
      return;
    }
    
    try {
      // 允许值是一个函数，类似于useState的setter
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      // 保存到state
      setStoredValue(valueToStore);
      
      // 保存到localStorage
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
      
      // 触发自定义事件，以便其他useLocalStorage钩子可以响应变化
      window.dispatchEvent(new Event('local-storage'));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);
  
  // 移除值的函数
  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(`Tried removing localStorage key "${key}" even though environment is not a client`);
      return;
    }
    
    try {
      // 从localStorage中移除
      window.localStorage.removeItem(key);
      
      // 重置state
      setStoredValue(initialValue);
      
      // 触发自定义事件
      window.dispatchEvent(new Event('local-storage'));
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [initialValue, key]);
  
  // 监听其他组件对localStorage的更改
  useEffect(() => {
    const handleStorageChange = () => {
      setStoredValue(readValue());
    };
    
    // 监听自定义事件和storage事件
    window.addEventListener('local-storage', handleStorageChange);
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('local-storage', handleStorageChange);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [readValue]);
  
  return [storedValue, setValue, removeValue];
};

export default useLocalStorage;