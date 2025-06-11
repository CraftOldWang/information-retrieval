import { useState, useEffect, useCallback } from 'react';
import useLocalStorage from './useLocalStorage';

/**
 * 主题钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 主题状态和方法
 */
const useTheme = (options = {}) => {
  const {
    defaultTheme = 'light',
    storageKey = 'theme',
    themes = ['light', 'dark']
  } = options;
  
  // 使用本地存储保存主题设置
  const [storedTheme, setStoredTheme, removeStoredTheme] = useLocalStorage(storageKey, defaultTheme);
  
  // 状态
  const [theme, setTheme] = useState(storedTheme);
  const [systemTheme, setSystemTheme] = useState(null);
  const [isSystemTheme, setIsSystemTheme] = useState(storedTheme === 'system');
  
  // 检测系统主题
  const detectSystemTheme = useCallback(() => {
    if (typeof window === 'undefined') return defaultTheme;
    
    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return isDarkMode ? 'dark' : 'light';
  }, [defaultTheme]);
  
  // 初始化系统主题
  useEffect(() => {
    setSystemTheme(detectSystemTheme());
  }, [detectSystemTheme]);
  
  // 监听系统主题变化
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      const newSystemTheme = e.matches ? 'dark' : 'light';
      setSystemTheme(newSystemTheme);
      
      if (isSystemTheme) {
        setTheme(newSystemTheme);
      }
    };
    
    // 添加监听器
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // 兼容旧版浏览器
      mediaQuery.addListener(handleChange);
    }
    
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        // 兼容旧版浏览器
        mediaQuery.removeListener(handleChange);
      }
    };
  }, [isSystemTheme]);
  
  // 当主题变化时应用到文档
  useEffect(() => {
    if (typeof document === 'undefined') return;
    
    const root = document.documentElement;
    const activeTheme = isSystemTheme ? systemTheme : theme;
    
    // 移除所有主题类
    themes.forEach(t => {
      root.classList.remove(`theme-${t}`);
    });
    
    // 添加当前主题类
    root.classList.add(`theme-${activeTheme}`);
    
    // 设置meta主题颜色
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', activeTheme === 'dark' ? '#1a1a1a' : '#ffffff');
    }
  }, [theme, systemTheme, isSystemTheme, themes]);
  
  // 切换主题
  const toggleTheme = useCallback(() => {
    if (isSystemTheme) {
      // 如果当前是系统主题，切换到明确的主题
      const newTheme = systemTheme === 'dark' ? 'light' : 'dark';
      setTheme(newTheme);
      setStoredTheme(newTheme);
      setIsSystemTheme(false);
    } else {
      // 在明确的主题之间切换
      const currentIndex = themes.indexOf(theme);
      const nextIndex = (currentIndex + 1) % themes.length;
      const newTheme = themes[nextIndex];
      
      if (newTheme === 'system') {
        setIsSystemTheme(true);
        setTheme(systemTheme);
      } else {
        setTheme(newTheme);
      }
      
      setStoredTheme(newTheme);
    }
  }, [theme, themes, systemTheme, isSystemTheme, setStoredTheme]);
  
  // 设置特定主题
  const setSpecificTheme = useCallback((newTheme) => {
    if (!themes.includes(newTheme)) {
      console.warn(`Theme "${newTheme}" is not defined in themes array`);
      return;
    }
    
    if (newTheme === 'system') {
      setIsSystemTheme(true);
      setTheme(systemTheme);
    } else {
      setIsSystemTheme(false);
      setTheme(newTheme);
    }
    
    setStoredTheme(newTheme);
  }, [themes, systemTheme, setStoredTheme]);
  
  // 重置为默认主题
  const resetTheme = useCallback(() => {
    if (defaultTheme === 'system') {
      setIsSystemTheme(true);
      setTheme(systemTheme);
    } else {
      setIsSystemTheme(false);
      setTheme(defaultTheme);
    }
    
    setStoredTheme(defaultTheme);
  }, [defaultTheme, systemTheme, setStoredTheme]);
  
  // 清除主题设置
  const clearTheme = useCallback(() => {
    removeStoredTheme();
    resetTheme();
  }, [removeStoredTheme, resetTheme]);
  
  return {
    // 状态
    theme: isSystemTheme ? systemTheme : theme,
    systemTheme,
    isSystemTheme,
    isDarkTheme: (isSystemTheme ? systemTheme : theme) === 'dark',
    isLightTheme: (isSystemTheme ? systemTheme : theme) === 'light',
    storedTheme,
    
    // 方法
    toggleTheme,
    setTheme: setSpecificTheme,
    resetTheme,
    clearTheme
  };
};

export default useTheme;