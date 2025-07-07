import React from 'react';
import './Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="footer">
      <div className="container footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h4>关于我们</h4>
            <p>NKU搜索引擎是一个基于向量空间模型的搜索引擎，支持网页和文档搜索。</p>
          </div>
          
          <div className="footer-section">
            <h4>功能</h4>
            <ul className="footer-links">
              <li><a href="/">网页搜索</a></li>
              <li><a href="/documents">文档搜索</a></li>
              <li><a href="/">个性化搜索</a></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4>联系我们</h4>
            <p>南开大学 计算机学院</p>
            <p>信息检索与数据挖掘课程项目</p>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>&copy; {currentYear} NKU搜索引擎 - 保留所有权利</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;