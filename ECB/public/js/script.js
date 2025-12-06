// 动态添加题目表单
let questionCount = 1;

function addQuestion() {
  const container = document.getElementById('questions-container');
  const questionDiv = document.createElement('div');
  questionDiv.className = 'question-item card';
  questionDiv.innerHTML = `
    <h4>题目 ${questionCount + 1}</h4>
    <div class="form-group">
      <label class="form-label">题目类型</label>
      <select name="type_${questionCount}" class="form-control question-type" onchange="updateQuestionType(${questionCount})">
        <option value="choice">选择题</option>
        <option value="fill">填空题</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">题目描述</label>
      <textarea name="question_${questionCount}" class="form-control" rows="2" placeholder="请输入题目描述..."></textarea>
    </div>
    <div class="form-group" id="options_${questionCount}">
      <label class="form-label">选项数量</label>
      <select name="optionCount_${questionCount}" class="form-control option-count" onchange="updateOptions(${questionCount})">
        <option value="2">2个选项</option>
        <option value="3">3个选项</option>
        <option value="4" selected>4个选项</option>
        <option value="5">5个选项</option>
        <option value="6">6个选项</option>
      </select>
      <div class="options-list mt-2" id="optionsList_${questionCount}">
        <!-- 选项将通过JavaScript动态生成 -->
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">正确答案</label>
      <input type="text" name="correctAnswer_${questionCount}" class="form-control" placeholder="请输入正确答案（如A、B、C或具体答案）">
    </div>
    <div class="form-group">
      <label class="form-label">题目解析（可选）</label>
      <textarea name="explanation_${questionCount}" class="form-control" rows="2" placeholder="请输入题目解析..."></textarea>
    </div>
    <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion(this)">删除此题</button>
  `;
  container.appendChild(questionDiv);
  questionCount++;
  
  // 初始化新题目的选项
  updateOptions(questionCount - 1);
}

function removeQuestion(button) {
  const questionDiv = button.closest('.question-item');
  questionDiv.remove();
  
  // 重新编号所有题目
  const questions = document.querySelectorAll('.question-item');
  questions.forEach((question, index) => {
    const questionNumber = index;
    const title = question.querySelector('h4');
    title.textContent = `题目 ${questionNumber + 1}`;
    
    // 更新所有输入字段的名称
    const inputs = question.querySelectorAll('[name^="type_"], [name^="question_"], [name^="optionCount_"], [name^="correctAnswer_"], [name^="explanation_"]');
    inputs.forEach(input => {
      const oldName = input.name;
      const parts = oldName.split('_');
      parts[1] = questionNumber;
      input.name = parts.join('_');
      
      if (input.classList.contains('question-type')) {
        input.setAttribute('onchange', `updateQuestionType(${questionNumber})`);
      }
      if (input.classList.contains('option-count')) {
        input.setAttribute('onchange', `updateOptions(${questionNumber})`);
      }
    });
    
    // 更新选项列表的ID
    const optionsDiv = question.querySelector(`[id^="options_"]`);
    const optionsList = question.querySelector(`[id^="optionsList_"]`);
    if (optionsDiv) optionsDiv.id = `options_${questionNumber}`;
    if (optionsList) optionsList.id = `optionsList_${questionNumber}`;
    
    // 重新生成选项
    if (question.querySelector('.option-count')) {
      updateOptions(questionNumber);
    }
  });
  
  questionCount = questions.length;
}

function updateQuestionType(questionIndex) {
  const questionDiv = document.querySelector(`[name="type_${questionIndex}"]`).closest('.question-item');
  const optionsDiv = questionDiv.querySelector(`#options_${questionIndex}`);
  const correctAnswerInput = questionDiv.querySelector(`[name="correctAnswer_${questionIndex}"]`);
  
  const type = document.querySelector(`[name="type_${questionIndex}"]`).value;
  
  if (type === 'choice') {
    optionsDiv.style.display = 'block';
    correctAnswerInput.placeholder = '请输入正确答案（如A、B、C等）';
  } else {
    optionsDiv.style.display = 'none';
    correctAnswerInput.placeholder = '请输入正确答案（具体答案）';
  }
}

function updateOptions(questionIndex) {
  const optionCount = parseInt(document.querySelector(`[name="optionCount_${questionIndex}"]`).value);
  const optionsList = document.getElementById(`optionsList_${questionIndex}`);
  
  optionsList.innerHTML = '';
  
  for (let i = 0; i < optionCount; i++) {
    const optionLetter = String.fromCharCode(65 + i); // A, B, C...
    const optionDiv = document.createElement('div');
    optionDiv.className = 'form-group';
    optionDiv.innerHTML = `
      <label class="form-label">选项 ${optionLetter}</label>
      <input type="text" name="option_${questionIndex}_${i}" class="form-control" placeholder="请输入选项 ${optionLetter} 的内容">
    `;
    optionsList.appendChild(optionDiv);
  }
}

// Markdown上传/粘贴切换
function toggleMarkdownInput() {
  const fileInput = document.getElementById('markdownFileInput');
  const textInput = document.getElementById('markdownTextInput');
  const toggleBtn = document.getElementById('toggleMarkdownBtn');
  
  if (fileInput.style.display === 'none') {
    fileInput.style.display = 'block';
    textInput.style.display = 'none';
    toggleBtn.textContent = '切换到文本输入';
  } else {
    fileInput.style.display = 'none';
    textInput.style.display = 'block';
    toggleBtn.textContent = '切换到文件上传';
  }
}

// 动态添加图片上传字段
function addImageUpload() {
  const container = document.getElementById('imageUploads');
  const newItem = document.createElement('div');
  newItem.className = 'image-upload-item';
  newItem.style.marginBottom = '1rem';
  newItem.innerHTML = `
    <div class="row" style="display: flex; gap: 10px; align-items: center;">
      <div style="flex: 1;">
        <input type="file" name="images" class="form-control" accept="image/*">
      </div>
      <div style="flex: 1;">
        <input type="text" name="imageNames" class="form-control" placeholder="图片名称">
      </div>
      <div>
        <button type="button" class="btn btn-danger btn-sm" onclick="removeImageUpload(this)">删除</button>
      </div>
    </div>
  `;
  container.appendChild(newItem);
}

function removeImageUpload(button) {
  const item = button.closest('.image-upload-item');
  item.remove();
}

// 文件上传预览
function previewMarkdownFile(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      document.getElementById('markdownText').value = e.target.result;
    };
    reader.readAsText(input.files[0]);
  }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
  // 初始化第一个题目的选项
  if (document.querySelector('.option-count')) {
    updateOptions(0);
  }
  
  // 表单验证
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      let isValid = true;
      const requiredFields = form.querySelectorAll('[required]');
      
      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          isValid = false;
          field.style.borderColor = '#e74c3c';
        } else {
          field.style.borderColor = '#ddd';
        }
      });
      
      if (!isValid) {
        e.preventDefault();
        alert('请填写所有必填字段');
      }
    });
  });
  
  // 自动隐藏消息提示
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      setTimeout(() => {
        alert.style.display = 'none';
      }, 300);
    }, 5000);
  });
  
  // 管理员删除表单验证
  const deleteForms = document.querySelectorAll('form[action*="/admin/delete-problem/"]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      const reasonInput = this.querySelector('input[name="reason"]');
      if (!reasonInput.value.trim()) {
        e.preventDefault();
        alert('请填写删除原因');
        reasonInput.focus();
      }
    });
  });
});
