const express = require('express');
const session = require('express-session');
const path = require('path');
const multer = require('multer');
const marked = require('marked');
const { JSDOM } = require('jsdom');
const createDOMPurify = require('dompurify');
const bcrypt = require('bcryptjs');
const dotenv = require('dotenv');
const fs = require('fs');
const fsExtra = require('fs-extra');
const mime = require('mime-types');
const db = require('./database');
const { isAuthenticated, isAdmin } = require('./auth');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// 确保上传目录存在
const uploadsDir = path.join(__dirname, 'uploads');
const problemsDir = path.join(__dirname, 'uploads', 'problems');
const tempDir = path.join(__dirname, 'uploads', 'temp');

[uploadsDir, problemsDir, tempDir].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// 配置 multer 用于临时文件上传
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, tempDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB限制
});

// 配置 marked 和 DOMPurify
const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

// 配置 marked 选项
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: true,
  highlight: function(code, lang) {
    return `<pre><code class="language-${lang}">${code}</code></pre>`;
  }
});

// 中间件配置
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static('public'));
app.use('/uploads', express.static('uploads'));

app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false }
}));

// 调试中间件
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  if (req.method === 'POST') {
    console.log('POST数据:', req.body);
  }
  next();
});

// 设置EJS模板引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 全局变量
app.use((req, res, next) => {
  res.locals.user = req.session.user || null;
  res.locals.isAdmin = req.session.user?.isAdmin || false;
  res.locals.success = null;
  res.locals.error = null;
  next();
});

// 辅助函数：从文件系统读取题目数据
async function getProblemData(problemId) {
  const problemDir = path.join(problemsDir, `problem_${problemId}`);
  
  if (!fs.existsSync(problemDir)) {
    return null;
  }
  
  try {
    // 读取题目元数据
    const metaPath = path.join(problemDir, 'meta.json');
    const questionsPath = path.join(problemDir, 'questions.json');
    const markdownPath = path.join(problemDir, 'problem.md');
    
    if (!fs.existsSync(metaPath) || !fs.existsSync(questionsPath)) {
      return null;
    }
    
    const metaData = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    const questionsData = JSON.parse(fs.readFileSync(questionsPath, 'utf8'));
    
    // 读取markdown内容（如果存在）
    let markdownContent = '';
    if (fs.existsSync(markdownPath)) {
      markdownContent = fs.readFileSync(markdownPath, 'utf8');
    }
    
    // 读取图片信息 - 只显示图片文件，不显示JSON文件
    const imagesDir = path.join(problemDir, 'images');
    let images = [];
    if (fs.existsSync(imagesDir)) {
      const imageFiles = fs.readdirSync(imagesDir);
      
      // 过滤只保留图片文件（排除.json文件）
      const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
      const actualImageFiles = imageFiles.filter(filename => {
        const ext = path.extname(filename).toLowerCase();
        return imageExtensions.includes(ext);
      });
      
      images = actualImageFiles.map(filename => {
        const imageMetaPath = path.join(problemDir, 'images', `${filename}.json`);
        let imageName = path.parse(filename).name;
        
        if (fs.existsSync(imageMetaPath)) {
          try {
            const imageMeta = JSON.parse(fs.readFileSync(imageMetaPath, 'utf8'));
            imageName = imageMeta.name || imageName;
          } catch (e) {
            console.error('读取图片元数据错误:', e);
          }
        }
        
        return {
          filename: filename,
          name: imageName,
          url: `/uploads/problems/problem_${problemId}/images/${filename}`
        };
      });
    }
    
    return {
      meta: metaData,
      questions: questionsData,
      markdown: markdownContent,
      images: images
    };
  } catch (error) {
    console.error('读取题目数据错误:', error);
    return null;
  }
}

// 辅助函数：获取题目数量
async function getProblemQuestionCount(problemId) {
  try {
    const problemData = await getProblemData(problemId);
    return problemData ? problemData.questions.length : 0;
  } catch (error) {
    console.error('获取题目数量错误:', error);
    return 0;
  }
}

// 路由
app.get('/', (req, res) => {
  res.render('home');
});

app.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/profile');
  }
  res.render('login');
});

app.get('/icons', (req, res) => {
  res.render('icons');
});

app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  
  try {
    const user = await db.getUserByUsername(username);
    if (!user) {
      return res.render('login', { error: '用户不存在' });
    }
    
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      return res.render('login', { error: '密码错误' });
    }
    
    req.session.user = {
      id: user.id,
      username: user.username,
      isAdmin: user.isAdmin === 1
    };
    
    res.redirect('/profile');
  } catch (error) {
    console.error('登录错误:', error);
    res.render('login', { error: '登录失败，请重试' });
  }
});

app.get('/register', (req, res) => {
  if (req.session.user) {
    return res.redirect('/profile');
  }
  res.render('register');
});

app.post('/register', async (req, res) => {
  const { username, password, confirmPassword } = req.body;
  
  if (password !== confirmPassword) {
    return res.render('register', { error: '两次输入的密码不一致' });
  }
  
  try {
    const existingUser = await db.getUserByUsername(username);
    if (existingUser) {
      return res.render('register', { error: '用户名已存在' });
    }
    
    const hashedPassword = await bcrypt.hash(password, 10);
    const userId = await db.createUser(username, hashedPassword);
    
    req.session.user = {
      id: userId,
      username: username,
      isAdmin: false
    };
    
    res.redirect('/profile');
  } catch (error) {
    console.error('注册错误:', error);
    res.render('register', { error: '注册失败，请重试' });
  }
});

app.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

app.get('/profile', isAuthenticated, async (req, res) => {
  try {
    const userStats = await db.getUserStats(req.session.user.id);
    const userProblems = await db.getAllProblemsByUser(req.session.user.id);
    
    // 为每个问题添加题目数量
    const userProblemsWithCount = await Promise.all(
      userProblems.map(async (problem) => {
        const questionCount = await getProblemQuestionCount(problem.id);
        return {
          ...problem,
          questionCount: questionCount
        };
      })
    );
    
    res.render('profile', { 
      userStats, 
      userProblems: userProblemsWithCount 
    });
  } catch (error) {
    console.error('获取用户资料错误:', error);
    res.redirect('/');
  }
});

app.post('/change-password', isAuthenticated, async (req, res) => {
  const { currentPassword, newPassword, confirmPassword } = req.body;
  
  if (newPassword !== confirmPassword) {
    return res.render('profile', { 
      error: '新密码两次输入不一致',
      userStats: await db.getUserStats(req.session.user.id),
      userProblems: await db.getAllProblemsByUser(req.session.user.id)
    });
  }
  
  try {
    const user = await db.getUserById(req.session.user.id);
    const isValidPassword = await bcrypt.compare(currentPassword, user.password);
    
    if (!isValidPassword) {
      return res.render('profile', { 
        error: '当前密码错误',
        userStats: await db.getUserStats(req.session.user.id),
        userProblems: await db.getAllProblemsByUser(req.session.user.id)
      });
    }
    
    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await db.updatePassword(req.session.user.id, hashedPassword);
    
    res.render('profile', { 
      success: '密码修改成功',
      userStats: await db.getUserStats(req.session.user.id),
      userProblems: await db.getAllProblemsByUser(req.session.user.id)
    });
  } catch (error) {
    console.error('修改密码错误:', error);
    res.render('profile', { 
      error: '修改密码失败',
      userStats: await db.getUserStats(req.session.user.id),
      userProblems: await db.getAllProblemsByUser(req.session.user.id)
    });
  }
});

app.get('/problems', async (req, res) => {
  try {
    const problems = await db.getAllProblems();
    
    // 为每个问题添加题目数量
    const problemsWithCount = await Promise.all(
      problems.map(async (problem) => {
        const questionCount = await getProblemQuestionCount(problem.id);
        return {
          ...problem,
          questionCount: questionCount
        };
      })
    );
    
    res.render('problems', { problems: problemsWithCount });
  } catch (error) {
    console.error('获取题目列表错误:', error);
    res.render('problems', { problems: [] });
  }
});

app.get('/problem/:id', async (req, res) => {
  try {
    const problem = await db.getProblemById(req.params.id);
    if (!problem) {
      return res.status(404).render('404');
    }
    
    // 从文件系统读取题目数据
    const problemData = await getProblemData(problem.id);
    if (!problemData) {
      return res.status(404).render('404', { error: '题目数据不存在' });
    }
    
    // 转换markdown为HTML
    let problemContent = '';
    if (problemData.markdown) {
      const rawMarkdown = problemData.markdown;
      const dirty = marked.parse(rawMarkdown);
      problemContent = DOMPurify.sanitize(dirty);
    }
    
    res.render('problem-detail', { 
      problem, 
      problemContent,
      images: problemData.images,
      questions: problemData.questions 
    });
  } catch (error) {
    console.error('获取题目详情错误:', error);
    res.status(500).send('服务器错误');
  }
});

app.post('/problem/:id/submit', isAuthenticated, async (req, res) => {
  const { answers } = req.body;
  const problemId = req.params.id;
  const userId = req.session.user.id;
  
  try {
    const problem = await db.getProblemById(problemId);
    if (!problem) {
      return res.status(404).render('404');
    }
    
    // 从文件系统读取题目数据
    const problemData = await getProblemData(problemId);
    if (!problemData) {
      return res.status(404).render('404');
    }
    
    const questions = problemData.questions;
    let correctCount = 0;
    const results = [];
    
    // 检查答案
    questions.forEach((question, index) => {
      const userAnswer = answers && answers[index] ? String(answers[index]).trim() : '';
      const correctAnswer = String(question.correctAnswer).trim();
      const isCorrect = userAnswer === correctAnswer;
      
      if (isCorrect) correctCount++;
      
      results.push({
        question: question.questionText || `第 ${index + 1} 题`,
        userAnswer,
        correctAnswer: correctAnswer,
        isCorrect,
        explanation: question.explanation || ''
      });
    });
    
    // 更新用户数据
    await db.updateUserStats(userId, questions.length, correctCount);
    
    // 更新题目答题数据
    await db.updateProblemStats(problemId, 1, correctCount);
    
    res.render('problem-result', {
      problem,
      results,
      totalQuestions: questions.length,
      correctCount,
      score: Math.round((correctCount / questions.length) * 100)
    });
  } catch (error) {
    console.error('提交答案错误:', error);
    res.status(500).send('提交答案失败');
  }
});

app.get('/create-problem', isAuthenticated, (req, res) => {
  res.render('create-problem');
});

app.post('/create-problem', isAuthenticated, upload.fields([
  { name: 'markdownFile', maxCount: 1 },
  { name: 'images', maxCount: 10 },
  { name: 'imageNames', maxCount: 10 }
]), async (req, res) => {
  const { 
    title, 
    markdownText, 
    questionCount,
    hasExplanation
  } = req.body;
  
  const userId = req.session.user.id;
  
  try {
    // 1. 先保存到数据库获取ID
    const dbProblemId = await db.createProblem({
      title,
      userId,
      hasExplanation: hasExplanation === 'true',
      problemDir: '' // 暂时为空，后面再更新
    });
    
    // 2. 创建题目文件夹
    const problemDirName = `problem_${dbProblemId}`;
    const problemDirPath = path.join(problemsDir, problemDirName);
    const imagesDirPath = path.join(problemDirPath, 'images');
    
    // 创建目录
    fs.mkdirSync(problemDirPath, { recursive: true });
    fs.mkdirSync(imagesDirPath, { recursive: true });
    
    let markdownContent = markdownText || '';
    
    // 3. 处理markdown文件上传
    if (req.files && req.files.markdownFile) {
      const markdownFile = req.files.markdownFile[0];
      markdownContent = fs.readFileSync(markdownFile.path, 'utf8');
      // 删除临时文件
      fs.unlinkSync(markdownFile.path);
    }
    
    // 4. 处理题目数据
    const questions = [];
    const questionCountInt = parseInt(questionCount) || 1;
    
    for (let i = 0; i < questionCountInt; i++) {
      const questionData = {
        questionText: req.body[`question_${i}`] || `问题 ${i + 1}`,
        type: req.body[`type_${i}`] || 'choice',
        correctAnswer: req.body[`correctAnswer_${i}`] || '',
        explanation: req.body[`explanation_${i}`] || ''
      };
      
      if (questionData.type === 'choice') {
        const optionCount = parseInt(req.body[`optionCount_${i}`]) || 4;
        questionData.options = [];
        
        for (let j = 0; j < optionCount; j++) {
          const optionKey = String.fromCharCode(65 + j);
          questionData.options.push({
            key: optionKey,
            text: req.body[`option_${i}_${j}`] || `选项 ${optionKey}`
          });
        }
      }
      
      questions.push(questionData);
    }
    
    // 5. 处理图片上传
    const images = [];
    if (req.files && req.files.images) {
      const imageFiles = req.files.images;
      const imageNames = req.body.imageNames || [];
      
      imageFiles.forEach((imageFile, index) => {
        const originalName = imageFile.originalname;
        const fileExt = path.extname(originalName);
        const fileName = `image_${Date.now()}_${index}${fileExt}`;
        const imageName = imageNames[index] || originalName.replace(fileExt, '');
        
        // 移动图片到题目文件夹
        const destPath = path.join(imagesDirPath, fileName);
        fs.renameSync(imageFile.path, destPath);
        
        // 保存图片元数据
        const imageMeta = {
          name: imageName,
          originalName: originalName,
          uploadedAt: new Date().toISOString()
        };
        
        fs.writeFileSync(
          path.join(imagesDirPath, `${fileName}.json`),
          JSON.stringify(imageMeta, null, 2)
        );
        
        images.push({
          filename: fileName,
          name: imageName
        });
      });
    }
    
    // 6. 保存文件到文件系统
    // 保存markdown文件
    fs.writeFileSync(
      path.join(problemDirPath, 'problem.md'),
      markdownContent
    );
    
    // 保存题目数据
    fs.writeFileSync(
      path.join(problemDirPath, 'questions.json'),
      JSON.stringify(questions, null, 2)
    );
    
    // 保存题目元数据
    const metaData = {
      title: title,
      userId: userId,
      createdAt: new Date().toISOString(),
      hasExplanation: hasExplanation === 'true',
      images: images
    };
    
    fs.writeFileSync(
      path.join(problemDirPath, 'meta.json'),
      JSON.stringify(metaData, null, 2)
    );
    
    // 7. 更新数据库中的文件夹路径
    await db.updateProblemDir(dbProblemId, problemDirName);
    
    res.redirect(`/problem/${dbProblemId}`);
  } catch (error) {
    console.error('创建题目错误:', error);
    res.status(500).send(`创建题目失败: ${error.message}`);
  }
});

app.post('/delete-problem/:id', isAuthenticated, async (req, res) => {
  const problemId = req.params.id;
  const userId = req.session.user.id;
  
  try {
    const problem = await db.getProblemById(problemId);
    
    // 检查是否是题目所有者或管理员
    if (problem.user_id !== userId && !req.session.user.isAdmin) {
      return res.status(403).send('无权删除此题目');
    }
    
    // 删除文件系统中的题目数据
    const problemDirPath = path.join(problemsDir, `problem_${problemId}`);
    if (fs.existsSync(problemDirPath)) {
      fsExtra.removeSync(problemDirPath);
    }
    
    // 删除数据库记录
    await db.deleteProblem(problemId);
    
    // 如果是发布者删除，更新上传题目数
    if (problem.user_id === userId) {
      await db.updateUserProblemCount(userId, -1);
    }
    
    res.redirect('/profile');
  } catch (error) {
    console.error('删除题目错误:', error);
    res.status(500).send('删除题目失败');
  }
});

app.post('/delete-record/:id', isAuthenticated, async (req, res) => {
  const problemId = req.params.id;
  const userId = req.session.user.id;
  
  console.log(`删除记录请求: problemId=${problemId}, userId=${userId}`);
  
  try {
    const problem = await db.getProblemById(problemId);
    
    if (!problem) {
      console.log(`题目 ${problemId} 不存在`);
      return res.status(404).send('题目不存在');
    }
    
    console.log(`找到题目:`, problem);
    
    // 检查是否是题目所有者
    if (problem.user_id !== userId) {
      console.log(`权限错误: 用户 ${userId} 尝试删除用户 ${problem.user_id} 的题目`);
      return res.status(403).send('无权删除此记录');
    }
    
    // 检查是否是已删除的题目
    if (problem.is_approved !== 0) {
      console.log(`题目 ${problemId} 不是已删除状态，is_approved=${problem.is_approved}`);
      return res.status(400).send('只能删除已被管理员删除的记录');
    }
    
    // 删除文件系统中的题目数据
    const problemDirPath = path.join(problemsDir, `problem_${problemId}`);
    if (fs.existsSync(problemDirPath)) {
      console.log(`删除文件系统数据: ${problemDirPath}`);
      fsExtra.removeSync(problemDirPath);
    } else {
      console.log(`文件系统数据不存在: ${problemDirPath}`);
    }
    
    // 从数据库中永久删除记录
    console.log(`从数据库永久删除记录: ${problemId}`);
    await db.deleteProblemPermanently(problemId);
    
    // 更新用户的上传题目数
    try {
      await db.updateUserProblemCount(userId, -1);
      console.log(`更新用户 ${userId} 的题目数: -1`);
    } catch (countError) {
      console.error('更新用户题目数错误:', countError);
    }
    
    console.log(`记录删除成功: ${problemId}`);
    res.redirect('/profile');
  } catch (error) {
    console.error('删除记录错误详情:', error);
    res.status(500).send(`删除记录失败: ${error.message}`);
  }
});

app.get('/ranking', async (req, res) => {
  try {
    const uploadRanking = await db.getUploadRanking();
    const correctRanking = await db.getCorrectRateRanking();
    res.render('ranking', { uploadRanking, correctRanking });
  } catch (error) {
    console.error('获取排名错误:', error);
    res.render('ranking', { uploadRanking: [], correctRanking: [] });
  }
});

// 管理员路由
app.get('/admin', isAdmin, async (req, res) => {
  try {
    const problems = await db.getAllProblemsForAdmin();
    
    // 为每个问题添加题目数量
    const problemsWithCount = await Promise.all(
      problems.map(async (problem) => {
        const questionCount = await getProblemQuestionCount(problem.id);
        return {
          ...problem,
          questionCount: questionCount
        };
      })
    );
    
    res.render('admin', { problems: problemsWithCount });
  } catch (error) {
    console.error('管理员页面错误:', error);
    res.status(500).send('服务器错误');
  }
});

app.post('/admin/delete-problem/:id', isAdmin, async (req, res) => {
  const { reason } = req.body;
  const problemId = req.params.id;
  
  console.log(`管理员删除题目: ID=${problemId}, 原因=${reason}`);
  
  try {
    // 删除文件系统中的题目数据
    const problemDirPath = path.join(problemsDir, `problem_${problemId}`);
    if (fs.existsSync(problemDirPath)) {
      fsExtra.removeSync(problemDirPath);
      console.log(`已删除文件系统数据: ${problemDirPath}`);
    }
    
    await db.adminDeleteProblem(problemId, reason);
    console.log(`已更新数据库记录: ID=${problemId}`);
    
    res.redirect('/admin');
  } catch (error) {
    console.error('管理员删除题目错误:', error);
    res.status(500).send('删除失败');
  }
});

// 错误处理
app.use((req, res, next) => {
  res.status(404).render('404');
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('服务器错误');
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在 http://localhost:${PORT}`);
  console.log('管理员账户: admin / admin123');
  console.log('测试用户: user / user123');
});