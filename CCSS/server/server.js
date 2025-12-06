const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const multer = require('multer');
const fs = require('fs');

// 初始化数据
require('./initData');

// 每周分数重置功能
require('./utils/scoreManager');

const studentRoutes = require('./routes/student');
const teacherRoutes = require('./routes/teacher');
const applicationRoutes = require('./routes/application');
const adminRoutes = require('./routes/admin');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../public')));
app.use('/applications', express.static(path.join(__dirname, 'data/applications')));
app.use('/FAQ', express.static(path.join(__dirname, '../public/FAQ')));


// 在server.js中修改CORS部分，添加更多安全头
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  
  // 为摄像头添加必要的HTTP头
  res.header('Cross-Origin-Opener-Policy', 'same-origin');
  res.header('Cross-Origin-Embedder-Policy', 'require-corp');
  res.header('Cross-Origin-Resource-Policy', 'cross-origin');
  
  // 添加Content Security Policy
  res.header('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: blob:; " +
    "media-src 'self' blob:; " +
    "connect-src 'self'"
  );
  
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// 文件上传配置
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadPath = path.join(__dirname, 'data/uploads');
    if (!fs.existsSync(uploadPath)) {
      fs.mkdirSync(uploadPath, { recursive: true });
    }
    cb(null, uploadPath);
  },
  filename: (req, file, cb) => {
    const safeFilename = file.originalname.replace(/[^a-zA-Z0-9.\-]/g, '_');
    cb(null, Date.now() + '-' + safeFilename);
  }
});

const upload = multer({ 
  storage,
  limits: {
    fileSize: 5 * 1024 * 1024
  }
});

// 路由
app.use('/api/student', studentRoutes);
app.use('/api/teacher', teacherRoutes);
app.use('/api/application', upload.single('evidence'), applicationRoutes);
app.use('/api/admin', adminRoutes);

// 根路由
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>班级操行分系统</title></head>
      <body>
        <h1>班级操行分管理系统</h1>
        <ul>
          <li><a href="/student/login.html">学生端</a></li>
          <li><a href="/teacher/login.html">教师端</a></li>
          <li><a href="/admin/login.html">管理员</a></li>
          <li><a href="/application/submit.html">提交申请</a></li>
          <li><a href="/FAQ">常见问题解答</a></li>
        </ul>
      </body>
    </html>
  `);
});

// 错误处理中间件
app.use((error, req, res, next) => {
  console.error('服务器错误:', error);
  res.status(500).json({ 
    success: false, 
    message: '服务器内部错误' 
  });
});

// 404处理
app.use((req, res) => {
  res.status(404).json({ 
    success: false, 
    message: '接口不存在: ' + req.method + ' ' + req.path
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
  console.log(`学生端: http://localhost:${PORT}/student/login.html`);
  console.log(`教师端: http://localhost:${PORT}/teacher/login.html`);
  console.log(`管理员: http://localhost:${PORT}/admin/login.html`);
  console.log(`申请页面: http://localhost:${PORT}/application/submit.html`);
  console.log(`常见问题解答: http://localhost:${PORT}/FAQ`);
});
