import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { getSnapshot } from '../services/snapshotService';
import './SnapshotPage.css';

const SnapshotPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [snapshot, setSnapshot] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (!id) {
      setError('无效的快照ID');
      setIsLoading(false);
      return;
    }
    
    fetchSnapshot(id);
  }, [id]);
  
  const fetchSnapshot = async (snapshotId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getSnapshot(snapshotId);
      
      // API返回的是SnapshotResponse格式: { success: true, snapshot: {...} }
      if (response && response.snapshot) {
        const snapshotData = response.snapshot;
        setSnapshot({
          id: snapshotData.id,
          url: snapshotData.url,
          title: snapshotData.title,
          captureDate: snapshotData.timestamp,
          content: snapshotData.html_content
        });
      } else {
        setError('快照数据格式错误');
      }
      
      setIsLoading(false);
    } catch (err) {
      console.error('获取快照失败:', err);
      setError(err.message || '获取快照失败，请稍后再试');
      setIsLoading(false);
    }
  };
  
  const handleGoBack = () => {
    navigate(-1);
  };
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="snapshot-page">
      <Header />
      
      <main className="snapshot-content">
        {isLoading ? (
          <div className="loading-indicator">加载中...</div>
        ) : error ? (
          <div className="error-container">
            <div className="error-message">{error}</div>
            <button className="back-button" onClick={handleGoBack}>
              返回上一页
            </button>
          </div>
        ) : snapshot ? (
          <div className="snapshot-container">
            <div className="snapshot-header">
              <button className="back-button" onClick={handleGoBack}>
                返回搜索结果
              </button>
              <div className="snapshot-meta">
                <h1 className="snapshot-title">{snapshot.title}</h1>
                <div className="snapshot-url">{snapshot.url}</div>
                <div className="snapshot-date">
                  快照时间: {formatDate(snapshot.captureDate)}
                </div>
              </div>
            </div>
            
            <div className="snapshot-divider"></div>
            
            <div className="snapshot-frame-container">
              <div 
                className="snapshot-frame"
                dangerouslySetInnerHTML={{ __html: snapshot.content }}
              ></div>
            </div>
          </div>
        ) : (
          <div className="error-container">
            <div className="error-message">未找到快照</div>
            <button className="back-button" onClick={handleGoBack}>
              返回上一页
            </button>
          </div>
        )}
      </main>
      
       
    </div>
  );
};

export default SnapshotPage;