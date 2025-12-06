const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const xlsx = require('xlsx');
const { authenticateTeacher } = require('../utils/auth');

// 教师登录
router.post('/login', (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.json({ success: false, message: '用户名和密码不能为空' });
    }
    
    const teachersPath = path.join(__dirname, '../data/teachers.json');
    if (!fs.existsSync(teachersPath)) {
      return res.json({ success: false, message: '系统配置错误' });
    }
    
    const teachersData = fs.readFileSync(teachersPath, 'utf8');
    const teachers = JSON.parse(teachersData);
    const teacher = teachers.find(t => t.id === username && t.password === password);
    
    if (teacher) {
      res.json({ 
        success: true, 
        teacher: {
          id: teacher.id,
          name: teacher.name,
          subject: teacher.subject
        }
      });
    } else {
      res.json({ success: false, message: '用户名或密码错误' });
    }
  } catch (error) {
    console.error('教师登录处理错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 修改密码
router.post('/change-password', authenticateTeacher, (req, res) => {
  try {
    const { oldPassword, newPassword } = req.body;
    const teacherId = req.teacher.id;
    
    if (!oldPassword || !newPassword) {
      return res.json({ success: false, message: '密码不能为空' });
    }
    
    const teachersPath = path.join(__dirname, '../data/teachers.json');
    const teachers = JSON.parse(fs.readFileSync(teachersPath));
    const teacherIndex = teachers.findIndex(t => t.id === teacherId);
    
    if (teachers[teacherIndex].password !== oldPassword) {
      return res.json({ success: false, message: '原密码错误' });
    }
    
    teachers[teacherIndex].password = newPassword;
    fs.writeFileSync(teachersPath, JSON.stringify(teachers, null, 2));
    
    res.json({ success: true, message: '密码修改成功' });
  } catch (error) {
    console.error('修改密码错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取所有学生分数
router.get('/students-scores', authenticateTeacher, (req, res) => {
  try {
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据不存在' });
    }
    
    const students = JSON.parse(fs.readFileSync(studentsPath));
    
    const studentScores = students.map(student => {
      const scoreFile = path.join(scoresDir, `${student.id}.json`);
      let currentScore = 100;
      let records = [];
      
      if (fs.existsSync(scoreFile)) {
        try {
          const scoreData = JSON.parse(fs.readFileSync(scoreFile));
          currentScore = scoreData.currentScore || 100;
          records = scoreData.records || [];
        } catch (error) {
          console.error(`读取学生 ${student.id} 分数文件错误:`, error);
        }
      }
      
      return {
        id: student.id,
        name: student.name,
        class: student.class,
        currentScore,
        records
      };
    });
    
    res.json({ success: true, data: studentScores });
  } catch (error) {
    console.error('获取学生分数错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取小组排名数据
router.get('/class-ranks', authenticateTeacher, (req, res) => {
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

// 获取预定义原因列表
router.get('/reasons', authenticateTeacher, (req, res) => {
  try {
    const reasonsPath = path.join(__dirname, '../data/reasons.json');
    
    if (!fs.existsSync(reasonsPath)) {
      // 如果文件不存在，返回默认原因列表
      const defaultReasons = [
        "其他"
      ];
      return res.json({ success: true, data: defaultReasons });
    }
    
    const reasons = JSON.parse(fs.readFileSync(reasonsPath, 'utf8'));
    res.json({ success: true, data: reasons });
  } catch (error) {
    console.error('获取原因列表错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 直接给学生加分/扣分
router.post('/adjust-score', authenticateTeacher, (req, res) => {
  try {
    const { studentId, type, score, reason, subject, customReason } = req.body;
    const teacherId = req.teacher.id;
    
    if (!studentId || !type || !score || !subject) {
      return res.json({ success: false, message: '请填写完整信息' });
    }
    
    // 使用自定义原因或选择的原因
    const finalReason = customReason || reason;
    if (!finalReason) {
      return res.json({ success: false, message: '请填写原因' });
    }
    
    const scoreFile = path.join(__dirname, `../data/scores/${studentId}.json`);
    let scoreData = { currentScore: 100, records: [] };
    
    if (fs.existsSync(scoreFile)) {
      scoreData = JSON.parse(fs.readFileSync(scoreFile));
    }
    
    // 更新分数
    if (type === 'add') {
      scoreData.currentScore += parseInt(score);
    } else {
      scoreData.currentScore -= parseInt(score);
    }
    
    // 添加记录
    const record = {
      id: Date.now().toString(),
      type,
      score: parseInt(score),
      reason: finalReason,
      subject,
      teacherId,
      timestamp: new Date().toISOString()
    };
    
    scoreData.records.unshift(record);
    
    fs.writeFileSync(scoreFile, JSON.stringify(scoreData, null, 2));
    
    res.json({ success: true, message: '分数调整成功' });
  } catch (error) {
    console.error('分数调整错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取待审核申请
router.get('/pending-applications', authenticateTeacher, (req, res) => {
  try {
    const teacher = req.teacher;
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
              // 学科申请交由对应科目老师处理，其他交由班主任
              // 新增的扣分原因（常规、学习、生活）也交由班主任处理
              const isSubjectApplication = application.subject && 
                                          application.subject !== '非学科性' &&
                                          application.subject !== '常规' &&
                                          application.subject !== '学习' && 
                                          application.subject !== '生活';
              
              if (isSubjectApplication) {
                if (teacher.subject === application.subject) {
                  pendingApplications.push(application);
                }
              } else if (teacher.subject === '班主任') {
                pendingApplications.push(application);
              }
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

// 审核申请
router.post('/review-application', authenticateTeacher, (req, res) => {
  try {
    const { applicationId, action, score } = req.body;
    const teacherId = req.teacher.id;
    
    if (!applicationId || !action) {
      return res.json({ success: false, message: '参数不完整' });
    }
    
    const applicationDir = path.join(__dirname, `../data/applications/${applicationId}`);
    const applicationFile = path.join(applicationDir, 'application.json');
    //const applicationImgFile = path.join(applicationDir, "${application.evidence}");
    
    if (!fs.existsSync(applicationFile)) {
      return res.json({ success: false, message: '申请不存在' });
    }
    
    const application = JSON.parse(fs.readFileSync(applicationFile));
    
    if (action === 'approve') {
      // 更新学生分数
      const studentId = application.studentId;
      const scoreFile = path.join(__dirname, `../data/scores/${studentId}.json`);
      let scoreData = { currentScore: 100, records: [] };
      
      if (fs.existsSync(scoreFile)) {
        scoreData = JSON.parse(fs.readFileSync(scoreFile));
      }
      
      // 使用审核时设置的分数
      const finalScore = parseInt(score) || application.score;
      
      if (application.type === 'add') {
        scoreData.currentScore += finalScore;
      } else {
        scoreData.currentScore -= finalScore;
      }
      
      // 添加记录
      const record = {
        id: Date.now().toString(),
        type: application.type,
        score: finalScore,
        reason: application.reason,
        subject: application.subject,
        teacherId,
        timestamp: new Date().toISOString(),
        fromApplication: true,
        applicationId
      };
      
      scoreData.records.unshift(record);
      fs.writeFileSync(scoreFile, JSON.stringify(scoreData, null, 2));
    }
    
    // 删除申请文件夹
    fs.rmSync(applicationDir, { recursive: true, force: true });
    
    res.json({ success: true, message: `申请已${action === 'approve' ? '通过' : '拒绝'}` });
  } catch (error) {
    console.error('审核申请错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 导出Excel
router.get('/export-scores', authenticateTeacher, (req, res) => {
  try {
    const studentsPath = path.join(__dirname, '../data/students.json');
    const scoresDir = path.join(__dirname, '../data/scores');
    
    if (!fs.existsSync(studentsPath)) {
      return res.json({ success: false, message: '学生数据不存在' });
    }
    
    const students = JSON.parse(fs.readFileSync(studentsPath));
    
    const data = [];
    const currentWeek = getWeekNumber(new Date());
    
    students.forEach(student => {
      const scoreFile = path.join(scoresDir, `${student.id}.json`);
      let currentScore = 100;
      let weekRecords = [];
      
      if (fs.existsSync(scoreFile)) {
        try {
          const scoreData = JSON.parse(fs.readFileSync(scoreFile));
          currentScore = scoreData.currentScore || 100;
          
          // 筛选本周记录
          weekRecords = (scoreData.records || []).filter(record => {
            const recordWeek = getWeekNumber(new Date(record.timestamp));
            return recordWeek === currentWeek;
          });
        } catch (error) {
          console.error(`读取学生 ${student.id} 分数文件错误:`, error);
        }
      }
      
      const addScore = weekRecords.filter(r => r.type === 'add').reduce((sum, r) => sum + r.score, 0);
      const deductScore = weekRecords.filter(r => r.type === 'deduct').reduce((sum, r) => sum + r.score, 0);
      
      data.push({
        学号: student.id,
        姓名: student.name,
        小组: student.class,
        当前分数: currentScore,
        本周加分: addScore,
        本周扣分: deductScore
      });
    });
    
    const workbook = xlsx.utils.book_new();
    const worksheet = xlsx.utils.json_to_sheet(data);
    xlsx.utils.book_append_sheet(workbook, worksheet, '学生操行分');
    
    const excelBuffer = xlsx.write(workbook, { type: 'buffer', bookType: 'xlsx' });
    
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename=学生操行分_第${currentWeek}周.xlsx`);
    res.send(excelBuffer);
  } catch (error) {
    console.error('导出Excel错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

// 获取系统状态信息
router.get('/system-status', authenticateTeacher, (req, res) => {
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
