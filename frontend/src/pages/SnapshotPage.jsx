import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
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
    try {
      // 这里应该是从API获取快照数据的逻辑
      // 模拟API调用
      setTimeout(() => {
        // 模拟数据
        setSnapshot({
          id: snapshotId,
          url: 'https://example.com/article/information-retrieval',
          title: '信息检索系统概述',
          captureDate: new Date().toISOString(),
          content: `
            <html>
              <head>
                <title>信息检索系统概述</title>
                <style>
                  body { font-family: Arial, sans-serif; line-height: 1.6; }
                  h1 { color: #333; }
                  p { margin-bottom: 1em; }
                </style>
              </head>
              <body>
                <h1>信息检索系统概述</h1>
                <p>信息检索（Information Retrieval，简称IR）是指从大规模非结构化数据集合中找出满足用户需求的相关信息的过程。信息检索系统是实现信息检索功能的软件系统。</p>
                <p>随着互联网的发展，信息检索系统已经成为人们日常生活中不可或缺的工具。搜索引擎是最常见的信息检索系统，如Google、百度等。</p>
                <h2>信息检索系统的基本组成</h2>
                <p>一个典型的信息检索系统通常包括以下几个部分：</p>
                <ul>
                  <li>爬虫系统：负责从互联网上获取文档</li>
                  <li>索引系统：对文档进行处理并建立索引</li>
                  <li>查询处理：解析用户查询并在索引中检索</li>
                  <li>排序系统：对检索结果进行相关性排序</li>
                  <li>用户界面：与用户交互的界面</li>
                </ul>
                <h2>信息检索模型</h2>
                <p>信息检索模型是信息检索系统的核心，它决定了系统如何表示文档和查询，以及如何计算它们之间的相似度。常见的信息检索模型包括：</p>
                <ul>
                  <li>布尔模型：基于布尔逻辑的简单模型</li>
                  <li>向量空间模型：将文档和查询表示为向量，计算向量间的相似度</li>
                  <li>概率模型：基于概率理论的模型</li>
                  <li>语言模型：基于统计语言模型的方法</li>
                  <li>深度学习模型：利用神经网络进行文本表示和匹配</li>
                </ul>
                <h2>评价指标</h2>
                <p>评价信息检索系统性能的常用指标包括：</p>
                <ul>
                  <li>准确率（Precision）：检索结果中相关文档的比例</li>
                  <li>召回率（Recall）：被检索到的相关文档占所有相关文档的比例</li>
                  <li>F值（F-measure）：准确率和召回率的调和平均</li>
                  <li>平均准确率（Average Precision）：在不同召回水平上准确率的平均值</li>
                  <li>归一化折扣累积增益（NDCG）：考虑排序位置的评价指标</li>
                </ul>
              </body>
            </html>
          `
        });
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      console.error('获取快照失败:', err);
      setError('获取快照失败，请稍后再试');
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
      
      <Footer />
    </div>
  );
};

export default SnapshotPage;