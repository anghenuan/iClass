const fs = require('fs');
const path = require('path');

// 获取当前周数
function getCurrentWeek() {
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const days = Math.floor((now - startOfYear) / (24 * 60 * 60 * 1000));
  const weekNumber = Math.ceil((days + 1) / 7);
  return weekNumber;
}

// 检查并重置每周分数
function checkAndResetWeeklyScores() {
  try {
    const scoresDir = path.join(__dirname, '../data/scores');
    const weekFile = path.join(__dirname, '../data/lastResetWeek.json');
    
    // 确保目录存在
    if (!fs.existsSync(scoresDir)) {
      fs.mkdirSync(scoresDir, { recursive: true });
    }
    
    const currentWeek = getCurrentWeek();
    let lastResetWeek = 0;
    
    // 读取上次重置周数
    if (fs.existsSync(weekFile)) {
      const weekData = JSON.parse(fs.readFileSync(weekFile, 'utf8'));
      lastResetWeek = weekData.lastResetWeek || 0;
    }
    
    // 如果到了新的一周，重置所有学生分数
    if (currentWeek !== lastResetWeek) {
      console.log(`检测到新的一周，重置学生分数 (第${currentWeek}周)`);
      
      const studentsPath = path.join(__dirname, '../data/students.json');
      if (fs.existsSync(studentsPath)) {
        const students = JSON.parse(fs.readFileSync(studentsPath, 'utf8'));
        
        students.forEach(student => {
          const scoreFile = path.join(scoresDir, `${student.id}.json`);
          const resetData = {
            currentScore: 100,
            records: [],
            lastResetWeek: currentWeek
          };
          
          fs.writeFileSync(scoreFile, JSON.stringify(resetData, null, 2));
        });
      }
      
      // 更新上次重置周数
      fs.writeFileSync(weekFile, JSON.stringify({ lastResetWeek: currentWeek }, null, 2));
      console.log('学生分数重置完成');
    }
  } catch (error) {
    console.error('重置学生分数错误:', error);
  }
}

// 初始化重置检查
checkAndResetWeeklyScores();

// 每小时检查一次是否需要重置
//setInterval(checkAndResetWeeklyScores, 60 * 60 * 1000);

module.exports = {
  getCurrentWeek,
  checkAndResetWeeklyScores
};
