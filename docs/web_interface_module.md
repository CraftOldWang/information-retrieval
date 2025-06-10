# Web 界面模块

## 概述

Web 界面模块负责提供用户友好的搜索引擎前端界面，实现用户与搜索引擎的交互。虽然作业不强调界面美观度，以功能为主，但良好的界面设计可以提升用户体验和系统可用性。本模块将使用 React 和 JavaScript 实现前端界面。

## 技术选择

### React 框架

选择 React 作为前端框架的理由：

1. **组件化开发**: 模块化设计，便于维护和扩展
2. **虚拟 DOM**: 高效的 DOM 更新机制，提升性能
3. **丰富的生态**: 大量可用的 UI 组件库和工具
4. **状态管理**: 通过 React Hooks 或 Redux 管理状态
5. **社区支持**: 活跃的社区和丰富的学习资源

### 其他技术

1. **Axios**: 用于 API 请求
2. **Ant Design**: 提供现成的 UI 组件
3. **SCSS/LESS**: 结构化的样式表
4. **React Router**: 实现前端路由

## 界面设计

### 总体布局

1. **响应式设计**: 适配不同屏幕尺寸
2. **简洁明了**: 简单的界面，突出搜索功能
3. **统一风格**: 采用南开大学校色和风格

### 页面结构

1. **首页**: 大型搜索框，类似 Google 首页
2. **结果页**: 搜索框+结果列表+筛选器
3. **高级搜索页**: 提供多条件复杂查询界面
4. **用户页面**: 用户登录、注册和个人设置
5. **历史记录页**: 展示用户搜索历史

## 功能组件

### 搜索组件

1. **搜索框**: 支持自动完成和搜索建议
2. **搜索按钮**: 提交查询
3. **语音搜索**: 支持语音输入(可选)
4. **搜索类型选择**: 普通/短语/通配/文档查询切换

### 结果展示组件

1. **结果列表**: 分页展示搜索结果
2. **摘要显示**: 显示网页摘要和关键词高亮
3. **快照链接**: 提供网页快照访问
4. **相关度指示**: 显示结果相关度

### 用户交互组件

1. **登录/注册**: 用户认证界面
2. **用户设置**: 个性化偏好配置
3. **收藏功能**: 允许用户收藏结果
4. **反馈机制**: 收集用户对结果的反馈

### 高级功能组件

1. **时间筛选**: 按时间范围过滤结果
2. **文件类型筛选**: 按文档类型过滤
3. **来源筛选**: 按网站域名过滤
4. **排序选项**: 提供不同排序方式

## 页面设计

### 首页

![首页设计草图](../docs/images/homepage_sketch.png)

```jsx
// 首页组件示例
function HomePage() {
    return (
        <div className="home-container">
            <div className="logo">NKU Search</div>
            <SearchBox placeholder="搜索南开资源..." showSuggestions={true} />
            <div className="search-options">
                <button>站内搜索</button>
                <button>文档搜索</button>
            </div>
        </div>
    );
}
```

### 结果页面

![结果页设计草图](../docs/images/resultspage_sketch.png)

```jsx
// 结果页组件示例
function ResultsPage() {
    return (
        <div className="results-container">
            <div className="header">
                <Logo size="small" />
                <SearchBox value={query} showSuggestions={true} />
            </div>
            <div className="filters">
                <FilterPanel
                    timeFilter={timeRange}
                    typeFilter={documentTypes}
                    domainFilter={domains}
                />
            </div>
            <div className="results">
                <ResultsList
                    results={searchResults}
                    highlightTerms={queryTerms}
                />
                <Pagination current={currentPage} total={totalResults} />
            </div>
            <div className="sidebar">
                <RelatedQueries queries={relatedQueries} />
            </div>
        </div>
    );
}
```

## 交互流程

1. **搜索流程**:

    - 用户输入查询词
    - 系统提供实时建议
    - 用户选择或继续输入并提交
    - 系统展示结果页面

2. **筛选流程**:

    - 用户在结果页面选择筛选条件
    - 系统实时更新结果
    - 用户可以组合多个筛选条件

3. **用户认证流程**:
    - 用户点击登录/注册
    - 填写表单并提交
    - 系统验证并创建会话
    - 重定向到个性化搜索页面

## API 集成

前端通过 RESTful API 与后端交互：

1. **搜索 API**: 发送查询并获取结果
2. **用户 API**: 处理用户认证和偏好设置
3. **建议 API**: 获取查询建议和自动完成
4. **反馈 API**: 发送用户反馈信息

## 响应式设计

确保在不同设备上的良好体验：

1. **桌面版**: 完整布局，多列展示
2. **平板版**: 简化布局，保留主要功能
3. **移动版**: 单列布局，重点突出搜索和结果

## 性能优化

1. **懒加载**: 延迟加载非关键资源
2. **组件分割**: 按需加载组件
3. **缓存机制**: 缓存查询结果和静态资源
4. **防抖和节流**: 优化频繁触发的事件

## 实现计划

1. 设计 UI 原型和用户流程
2. 开发核心组件(搜索框、结果列表等)
3. 实现 API 集成
4. 开发用户认证和个性化功能
5. 优化响应式布局
6. 进行用户测试和性能优化
