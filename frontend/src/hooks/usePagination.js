import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { parseQueryString, buildQueryString } from '../utils/helpers';

/**
 * 分页钩子
 * @param {Object} options - 配置选项
 * @returns {Object} - 分页状态和方法
 */
const usePagination = (options = {}) => {
  const {
    initialPage = 1,
    initialPageSize = 10,
    totalItems = 0,
    siblingCount = 1,
    updateUrl = false,
    pageParam = 'page'
  } = options;
  
  const location = useLocation();
  const navigate = useNavigate();
  
  // 从URL获取页码
  const queryParams = parseQueryString(location.search);
  const urlPage = queryParams[pageParam] ? parseInt(queryParams[pageParam], 10) : null;
  
  // 状态
  const [currentPage, setCurrentPage] = useState(urlPage || initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  
  // 计算总页数
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  
  // 当URL中的页码变化时更新状态
  useEffect(() => {
    if (updateUrl && urlPage && urlPage !== currentPage) {
      setCurrentPage(urlPage);
    }
  }, [urlPage, currentPage, updateUrl]);
  
  // 当总项目数或页面大小变化时，确保当前页码有效
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(Math.max(1, totalPages));
    }
  }, [totalItems, pageSize, currentPage, totalPages]);
  
  // 处理页码变化
  const handlePageChange = useCallback((page) => {
    const newPage = Math.max(1, Math.min(page, totalPages));
    
    if (newPage !== currentPage) {
      setCurrentPage(newPage);
      
      // 如果需要更新URL
      if (updateUrl) {
        const newParams = { ...queryParams };
        
        if (newPage === 1) {
          // 如果是第一页，从URL中移除页码参数
          delete newParams[pageParam];
        } else {
          // 否则更新页码参数
          newParams[pageParam] = newPage.toString();
        }
        
        const queryString = buildQueryString(newParams);
        navigate(`${location.pathname}${queryString}`, { replace: true });
      }
    }
  }, [currentPage, totalPages, updateUrl, navigate, location.pathname, queryParams, pageParam]);
  
  // 处理页面大小变化
  const handlePageSizeChange = useCallback((newPageSize) => {
    const newTotalPages = Math.max(1, Math.ceil(totalItems / newPageSize));
    const newCurrentPage = Math.min(currentPage, newTotalPages);
    
    setPageSize(newPageSize);
    setCurrentPage(newCurrentPage);
  }, [currentPage, totalItems]);
  
  // 生成分页范围
  const getPaginationRange = useCallback(() => {
    const totalNumbers = siblingCount * 2 + 3; // 左右兄弟 + 当前页 + 首尾页
    const totalBlocks = totalNumbers + 2; // +2 是两个省略号
    
    if (totalPages <= totalBlocks) {
      // 如果总页数小于要显示的块数，直接返回所有页码
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    
    // 计算左右兄弟的索引范围
    const leftSiblingIndex = Math.max(currentPage - siblingCount, 1);
    const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages);
    
    // 是否显示左右省略号
    const shouldShowLeftDots = leftSiblingIndex > 2;
    const shouldShowRightDots = rightSiblingIndex < totalPages - 1;
    
    const firstPageIndex = 1;
    const lastPageIndex = totalPages;
    
    // 只显示右省略号
    if (!shouldShowLeftDots && shouldShowRightDots) {
      const leftItemCount = 3 + 2 * siblingCount;
      const leftRange = Array.from({ length: leftItemCount }, (_, i) => i + 1);
      
      return [...leftRange, '...', lastPageIndex];
    }
    
    // 只显示左省略号
    if (shouldShowLeftDots && !shouldShowRightDots) {
      const rightItemCount = 3 + 2 * siblingCount;
      const rightRange = Array.from(
        { length: rightItemCount },
        (_, i) => totalPages - rightItemCount + i + 1
      );
      
      return [firstPageIndex, '...', ...rightRange];
    }
    
    // 显示左右省略号
    if (shouldShowLeftDots && shouldShowRightDots) {
      const middleRange = Array.from(
        { length: rightSiblingIndex - leftSiblingIndex + 1 },
        (_, i) => leftSiblingIndex + i
      );
      
      return [firstPageIndex, '...', ...middleRange, '...', lastPageIndex];
    }
  }, [currentPage, totalPages, siblingCount]);
  
  return {
    // 状态
    currentPage,
    pageSize,
    totalPages,
    totalItems,
    
    // 方法
    setCurrentPage,
    setPageSize,
    handlePageChange,
    handlePageSizeChange,
    getPaginationRange
  };
};

export default usePagination;