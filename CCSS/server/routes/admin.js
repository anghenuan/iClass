const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

// 管理员登录
router.post('/login', (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.json({ success: false, message: '用户名和密码不能为空' });
    }
    
    if (username === 'admin' && password === 'admin') {
      res.json({ success: true });
    } else {
      res.json({ success: false, message: '管理员账号或密码错误' });
    }
  } catch (error) {
    console.error('管理员登录处理错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取所有学生
router.get('/students', (req, res) => {
  try {
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据文件不存在' });
    }
    
    const studentsData = fs.readFileSync(studentsPath, 'utf8');
    const students = JSON.parse(studentsData);
    
    const studentData = students.map(student => {
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
      
      return {
        id: student.id,
        name: student.name,
        class: student.class,
        currentScore
      };
    });
    
    res.json({ success: true, data: studentData });
  } catch (error) {
    console.error('获取学生数据错误:', error);
    res.status(500).json({ success: false, message: '获取学生数据失败' });
  }
});

// 直接调整学生分数
router.post('/adjust-score', (req, res) => {
  try {
    const { studentId, newScore } = req.body;
    
    if (!studentId || !newScore) {
      return res.json({ success: false, message: '参数不完整' });
    }
    
    const scoreFile = path.join(__dirname, `../data/scores/${studentId}.json`);
    let scoreData = { currentScore: 100, records: [] };
    
    if (fs.existsSync(scoreFile)) {
      scoreData = JSON.parse(fs.readFileSync(scoreFile));
    }
    
    const oldScore = scoreData.currentScore;
    scoreData.currentScore = parseInt(newScore);
    
    // 添加管理员操作记录
    const record = {
      id: Date.now().toString(),
      type: 'admin_adjust',
      score: parseInt(newScore) - oldScore,
      reason: '管理员直接调整',
      timestamp: new Date().toISOString(),
      adminOperation: true
    };
    
    scoreData.records.unshift(record);
    fs.writeFileSync(scoreFile, JSON.stringify(scoreData, null, 2));
    
    res.json({ success: true, message: '分数调整成功' });
  } catch (error) {
    console.error('分数调整错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取所有未审核申请
router.get('/pending-applications', (req, res) => {
  try {
    const applicationsDir = path.join(__dirname, '../data/applications');
    const pendingApplications = [];
    
    if (fs.existsSync(applicationsDir)) {
      const applicationDirs = fs.readdirSync(applicationsDir);
      
      applicationDirs.forEach(dir => {
        const applicationFile = path.join(applicationsDir, dir, 'application.json');
        if (fs.existsSync(applicationFile)) {
          try {
            const application = JSON.parse(fs.readFileSync(applicationFile));
            if (application.status === 'pending') {
              pendingApplications.push(application);
            }
          } catch (error) {
            console.error(`读取申请文件错误 ${applicationFile}:`, error);
          }
        }
      });
    }
    
    res.json({ success: true, data: pendingApplications });
  } catch (error) {
    console.error('获取待审核申请错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 删除未审核申请
router.delete('/application/:id', (req, res) => {
  try {
    const applicationId = req.params.id;
    const applicationDir = path.join(__dirname, `../data/applications/${applicationId}`);
    
    if (fs.existsSync(applicationDir)) {
      fs.rmSync(applicationDir, { recursive: true, force: true });
      res.json({ success: true, message: '申请已删除' });
    } else {
      res.json({ success: false, message: '申请不存在' });
    }
  } catch (error) {
    console.error('删除申请错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 手动重置所有学生分数
router.post('/reset-scores', (req, res) => {
  try {
    const { resetType } = req.body; // 'weekly' 或 'manual'
    
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    const weekFile = path.join(__dirname, '../data/lastResetWeek.json');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据不存在' });
    }
    
    const students = JSON.parse(fs.readFileSync(studentsPath, 'utf8'));
    const currentWeek = require('../utils/scoreManager').getCurrentWeek();
    
    students.forEach(student => {
      const scoreFile = path.join(scoresDir, `${student.id}.json`);
      const resetData = {
        currentScore: 100,
        records: [],
        lastResetWeek: currentWeek
      };
      
      fs.writeFileSync(scoreFile, JSON.stringify(resetData, null, 2));
    });
    
    // 更新上次重置周数
    fs.writeFileSync(weekFile, JSON.stringify({ lastResetWeek: currentWeek }, null, 2));
    
    const message = resetType === 'weekly' ? 
      '每周自动重置完成' : '手动重置所有学生分数完成';
    
    res.json({ success: true, message });
  } catch (error) {
    console.error('重置学生分数错误:', error);
    res.status(500).json({ success: false, message: '重置失败' });
  }
});

// 获取系统状态信息
router.get('/system-status', (req, res) => {
  try {
    const weekFile = path.join(__dirname, '../data/lastResetWeek.json');
    let lastResetWeek = 0;
    
    if (fs.existsSync(weekFile)) {
      const weekData = JSON.parse(fs.readFileSync(weekFile, 'utf8'));
      lastResetWeek = weekData.lastResetWeek || 0;
    }
    
    const currentWeek = require('../utils/scoreManager').getCurrentWeek();
    
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

// 获取小组排名数据
router.get('/class-ranks', (req, res) => {
  try {
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据不存在' });
    }
    
    const students = JSON.parse(fs.readFileSync(studentsPath));
    
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
    const classRanks = Object.keys(classGroups).map(className => {
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
    
    res.json({ success: true, data: classRanks });
  } catch (error) {
    console.error('获取小组排名错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

module.exports = router;
