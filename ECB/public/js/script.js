/* 基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f7fa;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 导航栏 */
.navbar {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 2rem;
  list-style: none;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-links a:hover {
  background-color: #34495e;
}

/* 主内容区 */
.main-content {
  min-height: calc(100vh - 140px);
  padding: 2rem 0;
}

/* 卡片样式 */
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 2rem;
  margin-bottom: 2rem;
}

/* 按钮样式 */
.btn {
  display: inline-block;
  padding: 0.5rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn:hover {
  background-color: #2980b9;
}

.btn-primary {
  background-color: #3498db;
}

.btn-success {
  background-color: #2ecc71;
}

.btn-danger {
  background-color: #e74c3c;
}

.btn-warning {
  background-color: #f39c12;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

/* 表单样式 */
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-control:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

/* 表格样式 */
.table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.table tr:hover {
  background-color: #f8f9fa;
}

.table-responsive {
  overflow-x: auto;
}

/* 表格行状态 */
.table-row-deleted {
  background-color: #fef5e7 !important;
}

.table-row-deleted:hover {
  background-color: #fef9e7 !important;
}

/* 状态标签样式 */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
  text-transform: uppercase;
}

.status-active {
  background-color: #d5f4e6;
  color: #27ae60;
}

.status-deleted {
  background-color: #fadbd8;
  color: #e74c3c;
}

/* 删除原因样式 */
.delete-reason {
  font-size: 0.9rem;
  color: #e74c3c;
  padding: 0.5rem;
  background-color: #fef5e7;
  border-left: 3px solid #f39c12;
  border-radius: 4px;
  margin-top: 0.5rem;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  gap: 0.5rem;
}

/* 题目样式 */
.problem-card {
  border-left: 4px solid #3498db;
  transition: transform 0.2s;
}

.problem-card:hover {
  transform: translateY(-2px);
}

.problem-title {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.problem-meta {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

/* Markdown 内容样式 */
.markdown-content {
  line-height: 1.8;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4 {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  color: #2c3e50;
}

.markdown-content p {
  margin-bottom: 1rem;
}

.markdown-content ul,
.markdown-content ol {
  margin-bottom: 1rem;
  padding-left: 2rem;
}

.markdown-content code {
  background-color: #f8f9fa;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-content pre {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.markdown-content pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-content blockquote {
  border-left: 4px solid #3498db;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #555;
  font-style: italic;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.markdown-content table th,
.markdown-content table td {
  border: 1px solid #ddd;
  padding: 0.5rem;
}

.markdown-content table th {
  background-color: #f8f9fa;
}

/* 答题表单 */
.question-item {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: #fafafa;
}

.question-text {
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2c3e50;
}

.options-list {
  list-style: none;
}

.option-item {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.option-item:hover {
  background-color: #e8f4fc;
}

.option-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.option-input {
  margin-right: 0.75rem;
}

.option-text {
  font-size: 1rem;
}

/* 结果页面 */
.result-correct {
  color: #27ae60;
  background-color: #d5f4e6;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.result-incorrect {
  color: #e74c3c;
  background-color: #fadbd8;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.result-explanation {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #3498db;
  margin-top: 1rem;
}

/* 图片网格 */
.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.image-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  padding: 1rem;
  text-align: center;
}

.image-item img {
  max-width: 100%;
  max-height: 200px;
  margin-bottom: 0.5rem;
}

/* 排名页面 */
.ranking-table {
  margin-top: 2rem;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.ranking-rank {
  font-size: 1.5rem;
  font-weight: bold;
  color: #3498db;
  min-width: 60px;
}

.ranking-info {
  flex: 1;
}

.ranking-score {
  font-weight: bold;
  color: #2c3e50;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-links {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .container {
    padding: 0 10px;
  }
  
  .card {
    padding: 1rem;
  }
  
  .table {
    font-size: 0.9rem;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}

/* 消息提示 */
.alert {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.alert-success {
  background-color: #d5f4e6;
  color: #27ae60;
  border: 1px solid #a3e9c4;
}

.alert-error {
  background-color: #fadbd8;
  color: #e74c3c;
  border: 1px solid #f5b7b1;
}

.alert-warning {
  background-color: #fef5e7;
  color: #f39c12;
  border: 1px solid #fad7a0;
}

/* 网格布局 */
.problems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

/* 英雄区域 */
.hero-section {
  text-align: center;
  padding: 4rem 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  margin-bottom: 2rem;
}

/* 功能卡片 */
.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature-card {
  text-align: center;
}

.feature-card i {
  font-size: 3rem;
  color: #3498db;
  margin-bottom: 1rem;
}

/* 行布局 */
.row {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 图标系统 */
.icon {
    display: inline-block;
    width: 1em;
    height: 1em;
    stroke-width: 0;
    stroke: currentColor;
    fill: currentColor;
    vertical-align: -0.125em;
}

.icon-sm {
    width: 0.875em;
    height: 0.875em;
}

.icon-md {
    width: 1.25em;
    height: 1.25em;
}

.icon-lg {
    width: 1.5em;
    height: 1.5em;
}

.icon-xl {
    width: 2em;
    height: 2em;
}

.icon-2xl {
    width: 3em;
    height: 3em;
}

/* 图标按钮 */
.icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background-color: #f8f9fa;
    color: #495057;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}

.icon-btn:hover {
    background-color: #e9ecef;
    color: #212529;
    transform: translateY(-1px);
}

.icon-btn-primary {
    background-color: #3498db;
    color: white;
}

.icon-btn-primary:hover {
    background-color: #2980b9;
}

.icon-btn-success {
    background-color: #2ecc71;
    color: white;
}

.icon-btn-success:hover {
    background-color: #27ae60;
}

.icon-btn-danger {
    background-color: #e74c3c;
    color: white;
}

.icon-btn-danger:hover {
    background-color: #c0392b;
}

.icon-btn-warning {
    background-color: #f39c12;
    color: white;
}

.icon-btn-warning:hover {
    background-color: #d68910;
}

/* 特性图标 */
.feature-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 4rem;
    height: 4rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.feature-icon-primary {
    background-color: rgba(52, 152, 219, 0.1);
    color: #3498db;
}

.feature-icon-success {
    background-color: rgba(46, 204, 113, 0.1);
    color: #2ecc71;
}

.feature-icon-warning {
    background-color: rgba(243, 156, 18, 0.1);
    color: #f39c12;
}

/* 状态图标 */
.status-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    margin-right: 0.5rem;
}

.status-icon-correct {
    background-color: #d5f4e6;
    color: #27ae60;
}

.status-icon-incorrect {
    background-color: #fadbd8;
    color: #e74c3c;
}

.status-icon-pending {
    background-color: #fef5e7;
    color: #f39c12;
}
