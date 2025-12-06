const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const fs = require('fs');
const path = require('path');

// 删除旧的数据库文件（如果存在）
const dbFile = 'database.sqlite';
if (fs.existsSync(dbFile)) {
  fs.unlinkSync(dbFile);
  console.log('已删除旧的数据库文件');
}

// 创建新的数据库连接
const db = new sqlite3.Database(dbFile);

console.log('开始创建数据库表...');

// 创建用户表
db.run(`
  CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    isAdmin INTEGER DEFAULT 0,
    problems_uploaded INTEGER DEFAULT 0,
    problems_solved INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`, function(err) {
  if (err) {
    console.error('创建用户表失败:', err.message);
    db.close();
    return;
  }
  console.log('用户表创建成功');
  
  // 创建题目表
  db.run(`
    CREATE TABLE problems (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      user_id INTEGER NOT NULL,
      has_explanation INTEGER DEFAULT 0,
      is_approved INTEGER DEFAULT 1,
      delete_reason TEXT,
      attempts INTEGER DEFAULT 0,
      correct_count INTEGER DEFAULT 0,
      problem_dir TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )
  `, function(err) {
    if (err) {
      console.error('创建题目表失败:', err.message);
      db.close();
      return;
    }
    console.log('题目表创建成功');
    
    // 创建管理员账户
    bcrypt.hash('admin123', 10, (err, hash) => {
      if (err) {
        console.error('加密密码失败:', err);
        db.close();
        return;
      }
      
      db.run(
        `INSERT INTO users (username, password, isAdmin) VALUES (?, ?, ?)`,
        ['admin', hash, 1],
        function(err) {
          if (err) {
            console.error('创建管理员账户失败:', err.message);
          } else {
            console.log('管理员账户创建成功: admin / admin123');
          }
          
          // 创建测试用户
          bcrypt.hash('user123', 10, (err, hash) => {
            if (err) {
              console.error('加密测试用户密码失败:', err);
              db.close();
              return;
            }
            
            db.run(
              `INSERT INTO users (username, password) VALUES (?, ?)`,
              ['user', hash],
              function(err) {
                if (err) {
                  console.error('创建测试用户失败:', err.message);
                } else {
                  console.log('测试用户创建成功: user / user123');
                }
                
                // 关闭数据库连接
                db.close((err) => {
                  if (err) {
                    console.error('关闭数据库连接失败:', err);
                  } else {
                    console.log('数据库初始化完成！');
                    console.log('现在可以运行: npm start');
                  }
                });
              }
            );
          });
        }
      );
    });
  });
});