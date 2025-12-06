const fs = require('fs');
const path = require('path');

// 学生认证中间件
function authenticateStudent(req, res, next) {
  try {
    const token = req.headers.authorization;
    
    if (!token) {
      return res.status(401).json({ success: false, message: '未提供认证令牌' });
    }
    
    const studentsPath = path.join(__dirname, '../data/students.json');
    if (!fs.existsSync(studentsPath)) {
      return res.status(500).json({ success: false, message: '系统配置错误' });
    }
    
    const studentsData = fs.readFileSync(studentsPath, 'utf8');
    const students = JSON.parse(studentsData);
    const student = students.find(s => s.id === token);
    
    if (student) {
      req.student = student;
      next();
    } else {
      res.status(401).json({ success: false, message: '认证失败' });
    }
  } catch (error) {
    console.error('学生认证错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
}

// 教师认证中间件
function authenticateTeacher(req, res, next) {
  try {
    const token = req.headers.authorization;
    
    if (!token) {
      return res.status(401).json({ success: false, message: '未提供认证令牌' });
    }
    
    const teachersPath = path.join(__dirname, '../data/teachers.json');
    if (!fs.existsSync(teachersPath)) {
      return res.status(500).json({ success: false, message: '系统配置错误' });
    }
    
    const teachersData = fs.readFileSync(teachersPath, 'utf8');
    const teachers = JSON.parse(teachersData);
    const teacher = teachers.find(t => t.id === token);
    
    if (teacher) {
      req.teacher = teacher;
      next();
    } else {
      res.status(401).json({ success: false, message: '认证失败' });
    }
  } catch (error) {
    console.error('教师认证错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
}

module.exports = {
  authenticateStudent,
  authenticateTeacher
};
