const fs = require('fs');
const path = require('path');

// 确保数据目录存在
const dataDir = path.join(__dirname, 'data');
const applicationsDir = path.join(dataDir, 'applications');
const scoresDir = path.join(dataDir, 'scores');
const uploadsDir = path.join(dataDir, 'uploads');

[dataDir, applicationsDir, scoresDir, uploadsDir].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`创建目录: ${dir}`);
  }
});

// 初始化学生数据
const studentsData = [
  {
    "id": "1",
    "name": "测试账户1",
    "password": "123456",
    "class": "2组"
  },
  {
    "id": "2",
    "name": "测试账户2",
    "password": "123456",
    "class": "5组"
  },
  {
    "id": "3",
    "name": "测试账户3",
    "password": "123456",
    "class": "5组"
  },
  {
    "id": "4",
    "name": "测试账户4",
    "password": "123456",
    "class": "5组"
  },
  {
    "id": "5",
    "name": "测试账户5",
    "password": "123456",
    "class": "3组"
  },
  {
    "id": "6",
    "name": "测试账户6",
    "password": "123456",
    "class": "1组"
  },
  {
    "id": "7",
    "name": "测试账户7",
    "password": "123456",
    "class": "6组"
  },
  {
    "id": "8",
    "name": "测试账户8",
    "password": "123456",
    "class": "1组"
  },
  {
    "id": "9",
    "name": "测试账户9",
    "password": "123456",
    "class": "5组"
  },
  {
    "id": "10",
    "name": "测试账户10",
    "password": "123456",
    "class": "4组"
  },
  {
    "id": "11",
    "name": "测试账户11",
    "password": "123456",
    "class": "6组"
  },
  {
    "id": "12",
    "name": "测试账户12",
    "password": "123456",
    "class": "2组"
  },
];

// 初始化教师数据
const teachersData = [
  {
    "id": "T000",
    "name": "老师",
    "password": "123456",
    "subject": "班主任"
  },
  {
    "id": "T001",
    "name": "老师",
    "password": "123456",
    "subject": "数学"
  },
  {
    "id": "T002",
    "name": "老师",
    "password": "123456",
    "subject": "英语"
  },
  {
    "id": "T003",
    "name": "老师",
    "password": "123456",
    "subject": "物理"
  },
  {
    "id": "T004",
    "name": "老师",
    "password": "123456",
    "subject": "政治"
  },
  {
    "id": "T005",
    "name": "老师",
    "password": "123456",
    "subject": "历史"
  },
  {
    "id": "T006",
    "name": "老师",
    "password": "123456",
    "subject": "地理"
  },
  {
    "id": "T007",
    "name": "老师",
    "password": "123456",
    "subject": "生物"
  },
  {
    "id": "T008",
    "name": "老师",
    "password": "123456",
    "subject": "体育"
  },
  {
    "id": "T009",
    "name": "老师",
    "password": "123456",
    "subject": "信息技术"
  }
];

const reasonsData = [
  "课堂表现优秀",
  "作业完成良好", 
  "积极参加活动",
  "帮助同学",
  "进步明显",
  "考试优异",
  "竞赛获奖",
  "卫生值日认真",
  "班级贡献突出",
  "违反课堂纪律",
  "未完成作业",
  "迟到早退",
  "课堂喧哗",
  "不尊重师长",
  "打架斗殴",
  "破坏公物",
  "卫生值日不合格",
  "其他"
]

// 写入学生数据
const studentsPath = path.join(dataDir, 'students.json');
if (!fs.existsSync(studentsPath)) {
  fs.writeFileSync(studentsPath, JSON.stringify(studentsData, null, 2));
  console.log('学生数据初始化完成');
}

// 写入教师数据
const teachersPath = path.join(dataDir, 'teachers.json');
if (!fs.existsSync(teachersPath)) {
  fs.writeFileSync(teachersPath, JSON.stringify(teachersData, null, 2));
  console.log('教师数据初始化完成');
}

//写入常用原因
const reasonsPath = path.join(dataDir, 'reasons.json');
if (!fs.existsSync(reasonsPath)) {
  fs.writeFileSync(reasonsPath, JSON.stringify(reasonsData, null, 2));
  console.log('常用原因初始化完成');
}

// 初始化重置周数记录
const weekFile = path.join(dataDir, 'lastResetWeek.json');
if (!fs.existsSync(weekFile)) {
  const currentWeek = getCurrentWeek();
  fs.writeFileSync(weekFile, JSON.stringify({ lastResetWeek: currentWeek }, null, 2));
  console.log('重置周数记录初始化完成');
}

console.log('数据初始化完成！');

// 获取当前周数函数
function getCurrentWeek() {
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const days = Math.floor((now - startOfYear) / (24 * 60 * 60 * 1000));
  const weekNumber = Math.ceil((days + 1) / 7);
  return weekNumber;
}
