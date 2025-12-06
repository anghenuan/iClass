const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcryptjs');

const dbPath = path.join(__dirname, 'database.sqlite');
const db = new sqlite3.Database(dbPath);

// 用户相关函数
function getUserByUsername(username) {
  return new Promise((resolve, reject) => {
    db.get('SELECT * FROM users WHERE username = ?', [username], (err, row) => {
      if (err) {
        console.error(`查询用户 ${username} 错误:`, err);
        reject(err);
      } else {
        resolve(row);
      }
    });
  });
}

function getUserById(id) {
  return new Promise((resolve, reject) => {
    db.get('SELECT * FROM users WHERE id = ?', [id], (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function createUser(username, password) {
  return new Promise((resolve, reject) => {
    db.run(
      'INSERT INTO users (username, password) VALUES (?, ?)',
      [username, password],
      function(err) {
        if (err) reject(err);
        else resolve(this.lastID);
      }
    );
  });
}

function updatePassword(userId, newPassword) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE users SET password = ? WHERE id = ?',
      [newPassword, userId],
      (err) => {
        if (err) reject(err);
        else resolve();
      }
    );
  });
}

function getUserStats(userId) {
  return new Promise((resolve, reject) => {
    db.get(
      `SELECT 
        username,
        problems_uploaded,
        problems_solved,
        total_attempts,
        correct_attempts,
        CASE 
          WHEN total_attempts > 0 THEN ROUND((correct_attempts * 100.0 / total_attempts), 2)
          ELSE 0
        END as correct_rate
      FROM users WHERE id = ?`,
      [userId],
      (err, row) => {
        if (err) reject(err);
        else resolve(row);
      }
    );
  });
}

function updateUserStats(userId, totalQuestions, correctCount) {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run(
        'UPDATE users SET total_attempts = total_attempts + ?, correct_attempts = correct_attempts + ? WHERE id = ?',
        [totalQuestions, correctCount, userId],
        (err) => {
          if (err) reject(err);
        }
      );
      
      // 如果全部答对，增加已解决问题数
      if (correctCount === totalQuestions) {
        db.run(
          'UPDATE users SET problems_solved = problems_solved + 1 WHERE id = ?',
          [userId],
          (err) => {
            if (err) reject(err);
          }
        );
      }
      
      resolve();
    });
  });
}

function updateUserProblemCount(userId, change) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE users SET problems_uploaded = problems_uploaded + ? WHERE id = ?',
      [change, userId],
      function(err) {
        if (err) {
          console.error(`更新用户 ${userId} 题目数错误:`, err);
          reject(err);
        } else {
          console.log(`更新用户 ${userId} 题目数成功，影响行数: ${this.changes}`);
          resolve();
        }
      }
    );
  });
}

// 题目相关函数
function createProblem(problemData) {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run(
        `INSERT INTO problems 
        (title, user_id, has_explanation, problem_dir) 
        VALUES (?, ?, ?, ?)`,
        [
          problemData.title,
          problemData.userId,
          problemData.hasExplanation ? 1 : 0,
          problemData.problemDir || ''
        ],
        function(err) {
          if (err) {
            console.error('创建题目数据库记录错误:', err);
            reject(err);
            return;
          }
          
          const problemId = this.lastID;
          
          // 更新用户的上传题目数
          db.run(
            'UPDATE users SET problems_uploaded = problems_uploaded + 1 WHERE id = ?',
            [problemData.userId],
            (err) => {
              if (err) {
                console.error('更新用户题目数错误:', err);
                reject(err);
              } else {
                resolve(problemId);
              }
            }
          );
        }
      );
    });
  });
}

function updateProblemDir(problemId, problemDir) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE problems SET problem_dir = ? WHERE id = ?',
      [problemDir, problemId],
      function(err) {
        if (err) {
          console.error(`更新题目 ${problemId} 文件夹路径错误:`, err);
          reject(err);
        } else {
          console.log(`更新题目 ${problemId} 文件夹路径成功: ${problemDir}`);
          resolve();
        }
      }
    );
  });
}

function getAllProblems() {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT p.*, u.username 
       FROM problems p 
       JOIN users u ON p.user_id = u.id 
       WHERE p.is_approved = 1 
       ORDER BY p.created_at DESC`,
      (err, rows) => {
        if (err) {
          console.error('获取所有题目错误:', err);
          reject(err);
        } else {
          resolve(rows);
        }
      }
    );
  });
}

function getAllProblemsForAdmin() {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT p.*, u.username 
       FROM problems p 
       JOIN users u ON p.user_id = u.id 
       ORDER BY p.created_at DESC`,
      (err, rows) => {
        if (err) {
          console.error('获取管理员题目列表错误:', err);
          reject(err);
        } else {
          resolve(rows);
        }
      }
    );
  });
}

function getProblemById(id) {
  return new Promise((resolve, reject) => {
    db.get(
      `SELECT p.*, u.username 
       FROM problems p 
       LEFT JOIN users u ON p.user_id = u.id 
       WHERE p.id = ?`,
      [id],
      (err, row) => {
        if (err) {
          console.error(`查询题目 ${id} 错误:`, err);
          reject(err);
        } else {
          resolve(row);
        }
      }
    );
  });
}

function getAllProblemsByUser(userId) {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT * FROM problems 
       WHERE user_id = ? 
       ORDER BY created_at DESC`,
      [userId],
      (err, rows) => {
        if (err) {
          console.error(`获取用户 ${userId} 的题目错误:`, err);
          reject(err);
        } else {
          resolve(rows);
        }
      }
    );
  });
}

function updateProblemStats(problemId, attempts, correctCount) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE problems SET attempts = attempts + ?, correct_count = correct_count + ? WHERE id = ?',
      [attempts, correctCount, problemId],
      function(err) {
        if (err) {
          console.error(`更新题目 ${problemId} 统计数据错误:`, err);
          reject(err);
        } else {
          resolve();
        }
      }
    );
  });
}

function deleteProblem(problemId) {
  return new Promise((resolve, reject) => {
    db.run('DELETE FROM problems WHERE id = ?', [problemId], function(err) {
      if (err) {
        console.error(`删除题目 ${problemId} 错误:`, err);
        reject(err);
      } else {
        console.log(`删除题目 ${problemId} 成功，影响行数: ${this.changes}`);
        resolve();
      }
    });
  });
}

function deleteProblemPermanently(problemId) {
  return new Promise((resolve, reject) => {
    db.run('DELETE FROM problems WHERE id = ?', [problemId], function(err) {
      if (err) {
        console.error(`永久删除题目 ${problemId} 错误:`, err);
        reject(err);
      } else {
        console.log(`永久删除题目 ${problemId} 成功，影响行数: ${this.changes}`);
        resolve();
      }
    });
  });
}

function adminDeleteProblem(problemId, reason) {
  return new Promise((resolve, reject) => {
    console.log(`更新数据库: problemId=${problemId}, reason=${reason}`);
    db.run(
      'UPDATE problems SET is_approved = 0, delete_reason = ? WHERE id = ?',
      [reason, problemId],
      function(err) {
        if (err) {
          console.error('数据库更新错误:', err);
          reject(err);
        } else {
          console.log(`数据库更新成功，影响行数: ${this.changes}`);
          resolve();
        }
      }
    );
  });
}

// 排名相关函数
function getUploadRanking() {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT username, problems_uploaded 
       FROM users 
       ORDER BY problems_uploaded DESC 
       LIMIT 20`,
      (err, rows) => {
        if (err) {
          console.error('获取上传排名错误:', err);
          reject(err);
        } else {
          resolve(rows);
        }
      }
    );
  });
}

function getCorrectRateRanking() {
  return new Promise((resolve, reject) => {
    db.all(
      `SELECT 
        username,
        problems_solved,
        total_attempts,
        correct_attempts,
        CASE 
          WHEN total_attempts > 0 THEN ROUND((correct_attempts * 100.0 / total_attempts), 2)
          ELSE 0
        END as correct_rate
       FROM users 
       WHERE total_attempts >= 10 
       ORDER BY correct_rate DESC 
       LIMIT 20`,
      (err, rows) => {
        if (err) {
          console.error('获取正确率排名错误:', err);
          reject(err);
        } else {
          resolve(rows);
        }
      }
    );
  });
}

module.exports = {
  getUserByUsername,
  getUserById,
  createUser,
  updatePassword,
  getUserStats,
  updateUserStats,
  updateUserProblemCount,
  createProblem,
  updateProblemDir,
  getAllProblems,
  getAllProblemsForAdmin,
  getProblemById,
  getAllProblemsByUser,
  updateProblemStats,
  deleteProblem,
  deleteProblemPermanently,
  adminDeleteProblem,
  getUploadRanking,
  getCorrectRateRanking
};