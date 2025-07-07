import { useState, useEffect, useCallback } from 'react';

/**
 * 窗口大小钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 窗口大小状态和方法
 */
const useWindowSize = (options = {}) => {
  const {
    initialWidth = typeof window !== 'undefined' ? window.innerWidth : 1200,
    initialHeight = typeof window !== 'undefined' ? window.innerHeight : 800,
    debounceTime = 250
  } = options;
  
  // 状态
  const [windowSize, setWindowSize] = useState({
    width: initialWidth,
    height: initialHeight
  });
  
  // 防抖函数
  const debounce = (fn, ms) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  };
  
  // 处理窗口大小变化
  const handleResize = useCallback(() => {
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight
    });
  }, []);
  
  // 防抖处理的窗口大小变化函数
  const debouncedHandleResize = useCallback(
    debounce(handleResize, debounceTime),
    [handleResize, debounceTime]
  );
  
  // 监听窗口大小变化
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // 立即执行一次以获取初始大小
    handleResize();
    
    window.addEventListener('resize', debouncedHandleResize);
    
    return () => {
      window.removeEventListener('resize', debouncedHandleResize);
    };
  }, [handleResize, debouncedHandleResize]);
  
  // 检查是否为移动设备
  const isMobile = windowSize.width < 768;
  
  // 检查是否为平板设备
  const isTablet = windowSize.width >= 768 && windowSize.width < 1024;
  
  // 检查是否为桌面设备
  const isDesktop = windowSize.width >= 1024;
  
  // 获取当前设备类型
  const getDeviceType = () => {
    if (isMobile) return 'mobile';
    if (isTablet) return 'tablet';
    return 'desktop';
  };
  
  return {
    // 状态
    width: windowSize.width,
    height: windowSize.height,
    isMobile,
    isTablet,
    isDesktop,
    
    // 方法
    getDeviceType
  };
};

export default useWindowSize;