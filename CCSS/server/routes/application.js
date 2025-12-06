const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

// 提交加分申请
router.post('/submit', (req, res) => {
  try {
    const { studentName, subject, studentId } = req.body;
    const evidenceFile = req.file;
    
    if (!studentName || !subject || !studentId) {
      return res.json({ success: false, message: '请填写完整信息' });
    }
    
    // 检查是否频繁提交
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
          message: '操作太频繁，请稍后再试' 
        });
      }
    }
    
    // 创建申请
    const applicationId = Date.now().toString();
    const applicationDir = path.join(__dirname, `../data/applications/${applicationId}`);
    
    if (!fs.existsSync(applicationDir)) {
      fs.mkdirSync(applicationDir, { recursive: true });
    }
    
    const applicationData = {
      id: applicationId,
      studentId,
      studentName,
      type: 'add',
      score: 0,
      reason: '',
      subject,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    // 如果有凭证文件
    if (evidenceFile) {
      applicationData.evidence = evidenceFile.filename;
      
      // 将文件移动到申请目录
      const newPath = path.join(applicationDir, evidenceFile.filename);
      fs.renameSync(evidenceFile.path, newPath);
    }
    
    fs.writeFileSync(path.join(applicationDir, 'application.json'), JSON.stringify(applicationData, null, 2));
    
    res.json({ success: true, message: '申请提交成功' });
  } catch (error) {
    console.error('提交申请错误:', error);
    res.status(500).json({ success: false, message: '服务器错误' });
  }
});

module.exports = router;
