const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const { authenticateStudent } = require('../utils/auth');

// 学生登录
router.post('/login', (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.json({ success: false, message: '用户名和密码不能为空' });
    }
    
    const studentsPath = path.join(__dirname, '../data/students.json');
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '系统配置错误' });
    }
    
    const studentsData = fs.readFileSync(studentsPath, 'utf8');
    const students = JSON.parse(studentsData);
    const student = students.find(s => s.id === username && s.password === password);
    
    if (student) {
      res.json({ 
        success: true, 
        student: {
          id: student.id,
          name: student.name,
          class: student.class
        }
      });
    } else {
      res.json({ success: false, message: '用户名或密码错误' });
    }
  } catch (error) {
    console.error('学生登录处理错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 修改密码
router.post('/change-password', authenticateStudent, (req, res) => {
  try {
    const { oldPassword, newPassword } = req.body;
    const studentId = req.student.id;
    
    if (!oldPassword || !newPassword) {
      return res.json({ success: false, message: '密码不能为空' });
    }
    
    const studentsPath = path.join(__dirname, '../data/students.json');
    const students = JSON.parse(fs.readFileSync(studentsPath));
    const studentIndex = students.findIndex(s => s.id === studentId);
    
    if (students[studentIndex].password !== oldPassword) {
      return res.json({ success: false, message: '原密码错误' });
    }
    
    students[studentIndex].password = newPassword;
    fs.writeFileSync(studentsPath, JSON.stringify(students, null, 2));
    
    res.json({ success: true, message: '密码修改成功' });
  } catch (error) {
    console.error('修改密码错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取学生分数和记录
router.get('/score', authenticateStudent, (req, res) => {
  try {
    const studentId = req.student.id;
    const scoreFile = path.join(__dirname, `../data/scores/${studentId}.json`);
    
    if (fs.existsSync(scoreFile)) {
      const scoreData = JSON.parse(fs.readFileSync(scoreFile));
      res.json({ success: true, data: scoreData });
    } else {
      // 如果没有分数记录，返回默认分数
      res.json({ success: true, data: { currentScore: 100, records: [] } });
    }
  } catch (error) {
    console.error('获取学生分数错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 提交加分/扣分申请
router.post('/application', authenticateStudent, (req, res) => {
  try {
    const studentId = req.student.id;
    const { type, score, reason, subject } = req.body;
    
    if (!type || !score || !reason || !subject) {
      return res.json({ success: false, message: '请填写完整信息' });
    }
    
    // 检查是否频繁提交（同一科目1分钟内只能提交一次）
    const applicationsDir = path.join(__dirname, '../data/applications');
    if (fs.existsSync(applicationsDir)) {
      const applicationDirs = fs.readdirSync(applicationsDir);
      const now = Date.now();
      const recentApplications = [];
      
      applicationDirs.forEach(dir => {
        const applicationFile = path.join(applicationsDir, dir, 'application.json');
        if (fs.existsSync(applicationFile)) {
          try {
            const application = JSON.parse(fs.readFileSync(applicationFile));
            if (application.studentId === studentId && 
                application.subject === subject && 
                (now - parseInt(application.id)) < 1 * 60 * 1000) {
              recentApplications.push(application);
            }
          } catch (error) {
            console.error(`读取申请文件错误 ${applicationFile}:`, error);
          }
        }
      });
      
      if (recentApplications.length > 0) {
        return res.json({ 
          success: false, 
          message: '操作太频繁，请5分钟后再试' 
        });
      }
    }
    
    const applicationId = Date.now().toString();
    const applicationDir = path.join(__dirname, `../data/applications/${applicationId}`);
    
    if (!fs.existsSync(applicationDir)) {
      fs.mkdirSync(applicationDir, { recursive: true });
    }
    
    const applicationData = {
      id: applicationId,
      studentId,
      studentName: req.student.name,
      type,
      score: parseInt(score),
      reason,
      subject,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    fs.writeFileSync(path.join(applicationDir, 'application.json'), JSON.stringify(applicationData, null, 2));
    
    res.json({ success: true, message: '申请提交成功' });
  } catch (error) {
    console.error('提交申请错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取申请记录
router.get('/applications', authenticateStudent, (req, res) => {
  try {
    const studentId = req.student.id;
    const applicationsDir = path.join(__dirname, '../data/applications');
    const applications = [];
    
    if (fs.existsSync(applicationsDir)) {
      const applicationDirs = fs.readdirSync(applicationsDir);
      
      applicationDirs.forEach(dir => {
        const applicationFile = path.join(applicationsDir, dir, 'application.json');
        if (fs.existsSync(applicationFile)) {
          try {
            const application = JSON.parse(fs.readFileSync(applicationFile));
            if (application.studentId === studentId) {
              applications.push(application);
            }
          } catch (error) {
            console.error(`读取申请文件错误 ${applicationFile}:`, error);
          }
        }
      });
    }
    
    applications.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    res.json({ success: true, data: applications });
  } catch (error) {
    console.error('获取申请记录错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 提交扣分申诉
router.post('/appeal', authenticateStudent, (req, res) => {
  try {
    const studentId = req.student.id;
    const { recordId, reason, evidence } = req.body;
    
    if (!recordId || !reason) {
      return res.json({ success: false, message: '请填写完整信息' });
    }
    
    // 查找对应的扣分记录
    const scoreFile = path.join(__dirname, `../data/scores/${studentId}.json`);
    if (!fs.existsSync(scoreFile)) {
      return res.json({ success: false, message: '未找到扣分记录' });
    }
    
    const scoreData = JSON.parse(fs.readFileSync(scoreFile));
    const record = scoreData.records.find(r => r.id === recordId);
    
    if (!record) {
      return res.json({ success: false, message: '未找到对应的扣分记录' });
    }
    
    if (record.type !== 'deduct') {
      return res.json({ success: false, message: '只能对扣分记录进行申诉' });
    }
    
    // 创建申诉申请
    const appealId = Date.now().toString();
    const appealDir = path.join(__dirname, `../data/applications/${appealId}`);
    
    if (!fs.existsSync(appealDir)) {
      fs.mkdirSync(appealDir, { recursive: true });
    }
    
    const appealData = {
      id: appealId,
      studentId,
      studentName: req.student.name,
      type: 'appeal',
      recordId,
      originalScore: record.score,
      reason,
      evidence,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    fs.writeFileSync(path.join(appealDir, 'application.json'), JSON.stringify(appealData, null, 2));
    
    res.json({ success: true, message: '申诉提交成功' });
  } catch (error) {
    console.error('提交申诉错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 举报其他学生
router.post('/report', authenticateStudent, (req, res) => {
  try {
    const reporterId = req.student.id;
    const { reportedStudentId, reason, evidence, subject } = req.body;
    
    if (!reportedStudentId || !reason || !subject) {
      return res.json({ success: false, message: '请填写完整信息' });
    }
    
    // 检查被举报学生是否存在
    const studentsPath = path.join(__dirname, '../data/students.json');
    const students = JSON.parse(fs.readFileSync(studentsPath));
    const reportedStudent = students.find(s => s.id === reportedStudentId);
    
    if (!reportedStudent) {
      return res.json({ success: false, message: '被举报学生不存在' });
    }
    
    // 创建举报申请
    const reportId = Date.now().toString();
    const reportDir = path.join(__dirname, `../data/applications/${reportId}`);
    
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    const reportData = {
      id: reportId,
      type: 'report',
      reporterId,
      reporterName: req.student.name,
      reportedStudentId,
      reportedStudentName: reportedStudent.name,
      reason,
      evidence,
      subject,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    fs.writeFileSync(path.join(reportDir, 'application.json'), JSON.stringify(reportData, null, 2));
    
    res.json({ success: true, message: '举报提交成功' });
  } catch (error) {
    console.error('提交举报错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取小组排名数据（学生端只能看到自己小组和前三名）
router.get('/class-ranks', authenticateStudent, (req, res) => {
  try {
    const studentId = req.student.id;
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据不存在' });
    }
    
    const students = JSON.parse(fs.readFileSync(studentsPath));
    
    // 找到当前学生的小组
    const currentStudent = students.find(s => s.id === studentId);
    if (!currentStudent) {
      return res.json({ success: false, message: '学生信息不存在' });
    }
    
    const currentClass = currentStudent.class;
    
    // 按小组分组
    const classGroups = {};
    students.forEach(student => {
      if (!classGroups[student.class]) {
        classGroups[student.class] = [];
      }
      
      const scoreFile = path.join(scoresDir, `${student.id}.json`);
      let currentScore = 100;
      
      if (fs.existsSync(scoreFile)) {
        try {
          const scoreData = JSON.parse(fs.readFileSync(scoreFile));
          currentScore = scoreData.currentScore || 100;
        } catch (error) {
          console.error(`读取学生 ${student.id} 分数文件错误:`, error);
        }
      }
      
      classGroups[student.class].push({
        id: student.id,
        name: student.name,
        score: currentScore
      });
    });
    
    // 计算每个小组的平均分
    let classRanks = Object.keys(classGroups).map(className => {
      const students = classGroups[className];
      const totalScore = students.reduce((sum, student) => sum + student.score, 0);
      const averageScore = students.length > 0 ? (totalScore / students.length).toFixed(2) : 0;
      
      return {
        className,
        studentCount: students.length,
        averageScore: parseFloat(averageScore),
        students: students.sort((a, b) => b.score - a.score)
      };
    });
    
    // 按平均分排序
    classRanks.sort((a, b) => b.averageScore - a.averageScore);
    
    // 添加排名
    classRanks.forEach((classRank, index) => {
      classRank.rank = index + 1;
    });
    
    // 学生端只返回前三名和当前学生所在小组
    const topThree = classRanks.slice(0, 3);
    const currentClassRank = classRanks.find(rank => rank.className === currentClass);
    
    res.json({ 
      success: true, 
      data: {
        topThree,
        currentClass: currentClassRank
      }
    });
  } catch (error) {
    console.error('获取小组排名错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取系统状态信息
router.get('/system-status', authenticateStudent, (req, res) => {
  try {
    const weekFile = path.join(__dirname, '../data/lastResetWeek.json');
    let lastResetWeek = 0;
    
    if (fs.existsSync(weekFile)) {
      const weekData = JSON.parse(fs.readFileSync(weekFile, 'utf8'));
      lastResetWeek = weekData.lastResetWeek || 0;
    }
    
    const currentWeek = getWeekNumber(new Date());
    
    res.json({ 
      success: true, 
      data: {
        currentWeek,
        lastResetWeek,
        needReset: currentWeek !== lastResetWeek
      }
    });
  } catch (error) {
    console.error('获取系统状态错误:', error);
    res.status(500).json({ success: false, message: '获取系统状态失败' });
  }
});

// 获取周数辅助函数
function getWeekNumber(d) {
  d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  return weekNo;
}

module.exports = router;
