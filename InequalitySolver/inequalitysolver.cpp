#include "inequalitysolver.h"
#include <iostream>
#include <iomanip>
#include <sstream>

InequalitySolver::InequalitySolver(QWidget *parent)
    : QMainWindow(parent)
{
    setupUI();
    setWindowTitle("不等式整数解求解器");
    setMinimumSize(400, 700);
}

InequalitySolver::~InequalitySolver()
{
}

void InequalitySolver::setupUI()
{
    centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setSpacing(10);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    
    // 标题
    QLabel *titleLabel = new QLabel("不等式整数解求解器", this);
    titleLabel->setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;");
    titleLabel->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(titleLabel);
    
    // 输入区域
    inputGroup = new QGroupBox("输入不等式", this);
    QVBoxLayout *inputLayout = new QVBoxLayout(inputGroup);
    
    inequalityLabel = new QLabel("请输入不等式 (例如: 2x + 3 > x - 1):", this);
    inputLayout->addWidget(inequalityLabel);
    
    inequalityInput = new QLineEdit(this);
    inequalityInput->setPlaceholderText("例如: 2x + 3 > 5x - 2 或 x < 10");
    inequalityInput->setMinimumHeight(40);
    inequalityInput->setStyleSheet("font-size: 16px; padding: 5px;");
    inputLayout->addWidget(inequalityInput);
    
    exampleLabel = new QLabel("示例: 3x - 4 >= 2x + 1, x + 5 <= 10, 2x != 8", this);
    exampleLabel->setStyleSheet("color: #7f8c8d; font-style: italic;");
    inputLayout->addWidget(exampleLabel);
    
    mainLayout->addWidget(inputGroup);
    
    // 求解类型区域
    typeGroup = new QGroupBox("求解类型", this);
    QHBoxLayout *typeLayout = new QHBoxLayout(typeGroup);
    
    typeLabel = new QLabel("选择求解类型:", this);
    typeLayout->addWidget(typeLabel);
    
    typeComboBox = new QComboBox(this);
    typeComboBox->addItem("正整数解");
    typeComboBox->addItem("负整数解");
    typeComboBox->addItem("所有整数解");
    typeComboBox->setMinimumHeight(35);
    typeComboBox->setStyleSheet("font-size: 14px;");
    typeLayout->addWidget(typeComboBox);
    
    mainLayout->addWidget(typeGroup);
    
    // 按钮区域
    buttonGroup = new QGroupBox("操作", this);
    QHBoxLayout *buttonLayout = new QHBoxLayout(buttonGroup);
    
    solveButton = new QPushButton("求解", this);
    solveButton->setStyleSheet(
        "QPushButton {"
        "  background-color: #3498db;"
        "  color: white;"
        "  border: none;"
        "  padding: 10px 20px;"
        "  font-size: 16px;"
        "  border-radius: 5px;"
        "}"
        "QPushButton:hover {"
        "  background-color: #2980b9;"
        "}"
    );
    solveButton->setMinimumHeight(40);
    connect(solveButton, &QPushButton::clicked, this, &InequalitySolver::solveClicked);
    buttonLayout->addWidget(solveButton);
    
    clearButton = new QPushButton("清空", this);
    clearButton->setStyleSheet(
        "QPushButton {"
        "  background-color: #95a5a6;"
        "  color: white;"
        "  border: none;"
        "  padding: 10px 20px;"
        "  font-size: 16px;"
        "  border-radius: 5px;"
        "}"
        "QPushButton:hover {"
        "  background-color: #7f8c8d;"
        "}"
    );
    clearButton->setMinimumHeight(40);
    connect(clearButton, &QPushButton::clicked, this, &InequalitySolver::clearClicked);
    buttonLayout->addWidget(clearButton);
    
    exampleButton = new QPushButton("示例", this);
    exampleButton->setStyleSheet(
        "QPushButton {"
        "  background-color: #9b59b6;"
        "  color: white;"
        "  border: none;"
        "  padding: 10px 20px;"
        "  font-size: 16px;"
        "  border-radius: 5px;"
        "}"
        "QPushButton:hover {"
        "  background-color: #8e44ad;"
        "}"
    );
    exampleButton->setMinimumHeight(40);
    connect(exampleButton, &QPushButton::clicked, this, &InequalitySolver::exampleClicked);
    buttonLayout->addWidget(exampleButton);
    
    helpButton = new QPushButton("帮助", this);
    helpButton->setStyleSheet(
        "QPushButton {"
        "  background-color: #2ecc71;"
        "  color: white;"
        "  border: none;"
        "  padding: 10px 20px;"
        "  font-size: 16px;"
        "  border-radius: 5px;"
        "}"
        "QPushButton:hover {"
        "  background-color: #27ae60;"
        "}"
    );
    helpButton->setMinimumHeight(40);
    connect(helpButton, &QPushButton::clicked, this, &InequalitySolver::helpClicked);
    buttonLayout->addWidget(helpButton);
    
    mainLayout->addWidget(buttonGroup);
    
    // 标准形式显示
    QGroupBox *standardFormGroup = new QGroupBox("不等式标准形式", this);
    QVBoxLayout *standardFormLayout = new QVBoxLayout(standardFormGroup);
    
    standardFormDisplay = new QTextEdit(this);
    standardFormDisplay->setReadOnly(true);
    standardFormDisplay->setMaximumHeight(80);
    standardFormDisplay->setStyleSheet(
        "QTextEdit {"
        "  font-size: 14px;"
        "  font-family: 'Courier New', monospace;"
        "  background-color: #f8f9fa;"
        "  border: 1px solid #ddd;"
        "  border-radius: 5px;"
        "}"
    );
    standardFormLayout->addWidget(standardFormDisplay);
    
    mainLayout->addWidget(standardFormGroup);
    
    // 结果显示区域
    resultGroup = new QGroupBox("求解结果", this);
    QVBoxLayout *resultLayout = new QVBoxLayout(resultGroup);
    
    resultLabel = new QLabel("解集:", this);
    resultLabel->setStyleSheet("font-size: 16px; font-weight: bold;");
    resultLayout->addWidget(resultLabel);
    
    resultTable = new QTableWidget(this);
    resultTable->setColumnCount(2);
    resultTable->setHorizontalHeaderLabels(QStringList() << "序号" << "解");
    resultTable->horizontalHeader()->setStretchLastSection(true);
    resultTable->horizontalHeader()->setStyleSheet(
        "QHeaderView::section {"
        "  background-color: #3498db;"
        "  color: white;"
        "  padding: 5px;"
        "  font-weight: bold;"
        "}"
    );
    resultTable->verticalHeader()->setVisible(false);
    resultTable->setAlternatingRowColors(true);
    resultTable->setStyleSheet(
        "QTableWidget {"
        "  font-size: 14px;"
        "  selection-background-color: #bdc3c7;"
        "}"
        "QTableWidget::item {"
        "  padding: 5px;"
        "}"
    );
    resultLayout->addWidget(resultTable);
    
    mainLayout->addWidget(resultGroup);
    
    // 状态标签
    statusLabel = new QLabel("就绪", this);
    statusLabel->setStyleSheet(
        "QLabel {"
        "  background-color: #ecf0f1;"
        "  padding: 5px;"
        "  border-radius: 3px;"
        "  color: #7f8c8d;"
        "}"
    );
    statusLabel->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(statusLabel);
}

void InequalitySolver::solveClicked()
{
    QString input = inequalityInput->text().trimmed();
    if (input.isEmpty()) {
        displayError("请输入不等式！");
        return;
    }
    
    try {
        Inequality ineq = parseInequality(input.toStdString());
        
        // 显示标准形式
        string standardForm = "(";
        if (fabs(ineq.leftCoeff) > 1e-10) {
            if (fabs(ineq.leftCoeff - 1.0) < 1e-10) {
                standardForm += "x";
            } else if (fabs(ineq.leftCoeff + 1.0) < 1e-10) {
                standardForm += "-x";
            } else {
                standardForm += to_string((int)ineq.leftCoeff) + "x";
            }
            
            if (ineq.leftConst > 0) {
                standardForm += " + " + to_string((int)ineq.leftConst);
            } else if (ineq.leftConst < 0) {
                standardForm += " - " + to_string((int)(-ineq.leftConst));
            }
        } else {
            standardForm += to_string((int)ineq.leftConst);
        }
        
        standardForm += ") " + ineq.op + " (";
        
        if (fabs(ineq.rightCoeff) > 1e-10) {
            if (fabs(ineq.rightCoeff - 1.0) < 1e-10) {
                standardForm += "x";
            } else if (fabs(ineq.rightCoeff + 1.0) < 1e-10) {
                standardForm += "-x";
            } else {
                standardForm += to_string((int)ineq.rightCoeff) + "x";
            }
            
            if (ineq.rightConst > 0) {
                standardForm += " + " + to_string((int)ineq.rightConst);
            } else if (ineq.rightConst < 0) {
                standardForm += " - " + to_string((int)(-ineq.rightConst));
            }
        } else {
            standardForm += to_string((int)ineq.rightConst);
        }
        
        standardForm += ")";
        
        standardFormDisplay->setText(QString::fromStdString(standardForm));
        
        // 求解不等式
        int solutionType = typeComboBox->currentIndex() + 1; // 1-3
        vector<int> solutions = solveInequality(ineq, solutionType);
        
        // 显示结果
        displayResults(solutions, solutionType);
        
        statusLabel->setText(QString("求解完成，找到 %1 个解").arg(solutions.size()));
        
    } catch (const exception& e) {
        displayError(QString("错误: %1\n请检查输入格式是否正确。").arg(e.what()));
    }
}

void InequalitySolver::clearClicked()
{
    inequalityInput->clear();
    standardFormDisplay->clear();
    resultTable->clearContents();
    resultTable->setRowCount(0);
    resultLabel->setText("解集:");
    statusLabel->setText("已清空");
}

void InequalitySolver::exampleClicked()
{
    QStringList examples = {
        "2x + 3 > 5x - 2",
        "x < 10",
        "3x - 4 >= 2x + 1",
        "x + 5 <= 10",
        "2x != 8",
        "4x + 7 > 2x - 3",
        "x/2 - 3 <= 5"
    };
    
    static int exampleIndex = 0;
    inequalityInput->setText(examples[exampleIndex]);
    exampleIndex = (exampleIndex + 1) % examples.size();
    statusLabel->setText(QString("示例 %1").arg(exampleIndex + 1));
}

void InequalitySolver::helpClicked()
{
    QString helpText = 
        "<h2>不等式求解器使用说明</h2>"
        "<h3>支持的输入格式：</h3>"
        "<ul>"
        "<li><b>2x + 3 > 5x - 2</b></li>"
        "<li><b>x < 10</b></li>"
        "<li><b>3x - 4 >= 2x + 1</b></li>"
        "<li><b>x + 5 <= 10</b></li>"
        "<li><b>2x != 8</b></li>"
        "<li><b>4x + 7 > 2x - 3</b></li>"
        "<li><b>x/2 - 3 <= 5</b></li>"
        "</ul>"
        "<h3>支持的不等号：</h3>"
        "<p>>, <, >=, <=, !=</p>"
        "<h3>支持的求解类型：</h3>"
        "<ol>"
        "<li><b>正整数解</b> - x > 0</li>"
        "<li><b>负整数解</b> - x < 0</li>"
        "<li><b>所有整数解</b> - 所有整数</li>"
        "</ol>"
        "<h3>注意：</h3>"
        "<ul>"
        "<li>程序自动将分数转换为小数处理</li>"
        "<li>解的范围为 -100 到 100</li>"
        "<li>结果显示为整数</li>"
        "</ul>";
    
    QMessageBox::information(this, "帮助", helpText);
}

void InequalitySolver::parseExpression(const string& expr, double& coeff, double& constant)
{
    coeff = 0;
    constant = 0;
    
    string expression = expr;
    // 移除所有空格
    expression.erase(remove_if(expression.begin(), expression.end(), ::isspace), expression.end());
    
    // 如果表达式为空
    if (expression.empty()) {
        return;
    }
    
    // 处理分数
    size_t slashPos;
    while ((slashPos = expression.find('/')) != string::npos) {
        // 找到分数前面的数字
        size_t numStart = slashPos;
        while (numStart > 0 && (isdigit(expression[numStart - 1]) || expression[numStart - 1] == '.' || 
                               expression[numStart - 1] == 'x' || expression[numStart - 1] == 'X')) {
            numStart--;
        }
        
        // 找到分数后面的数字
        size_t denomEnd = slashPos + 1;
        while (denomEnd < expression.length() && (isdigit(expression[denomEnd]) || expression[denomEnd] == '.')) {
            denomEnd++;
        }
        
        string numStr = expression.substr(numStart, slashPos - numStart);
        string denomStr = expression.substr(slashPos + 1, denomEnd - slashPos - 1);
        
        if (!numStr.empty() && !denomStr.empty()) {
            double numerator = stod(numStr);
            double denominator = stod(denomStr);
            double value = numerator / denominator;
            
            string replacement = to_string(value);
            // 移除末尾的零
            size_t dotPos = replacement.find('.');
            if (dotPos != string::npos) {
                while (replacement.back() == '0') {
                    replacement.pop_back();
                }
                if (replacement.back() == '.') {
                    replacement.pop_back();
                }
            }
            
            expression.replace(numStart, denomEnd - numStart, replacement);
        }
    }
    
    // 在表达式前添加+号以便统一处理
    if (expression[0] != '+' && expression[0] != '-') {
        expression = "+" + expression;
    }
    
    size_t pos = 0;
    while (pos < expression.length()) {
        // 获取符号
        char sign = expression[pos];
        pos++;
        
        // 找到当前项的结束位置
        size_t term_end = pos;
        while (term_end < expression.length() && 
               expression[term_end] != '+' && 
               expression[term_end] != '-') {
            term_end++;
        }
        
        string term = expression.substr(pos, term_end - pos);
        
        if (term.find('x') != string::npos || term.find('X') != string::npos) {
            // 包含x的项
            size_t xPos = term.find_first_of("xX");
            string coeffStr = term.substr(0, xPos);
            
            double value;
            if (coeffStr.empty() || coeffStr == "+" || coeffStr == "-") {
                value = 1.0;
            } else {
                value = stod(coeffStr);
            }
            
            if (sign == '-') {
                coeff -= value;
            } else {
                coeff += value;
            }
        } else {
            // 常数项
            if (!term.empty()) {
                double value = stod(term);
                if (sign == '-') {
                    constant -= value;
                } else {
                    constant += value;
                }
            }
        }
        
        pos = term_end;
    }
}

Inequality InequalitySolver::parseInequality(const string& inequalityStr)
{
    Inequality ineq;
    ineq.leftCoeff = 0;
    ineq.leftConst = 0;
    ineq.rightCoeff = 0;
    ineq.rightConst = 0;
    
    string leftStr, rightStr;
    string op;
    
    // 查找不等号
    size_t pos;
    if ((pos = inequalityStr.find(">=")) != string::npos) {
        op = ">=";
    } else if ((pos = inequalityStr.find("<=")) != string::npos) {
        op = "<=";
    } else if ((pos = inequalityStr.find("!=")) != string::npos) {
        op = "!=";
    } else if ((pos = inequalityStr.find(">")) != string::npos) {
        op = ">";
    } else if ((pos = inequalityStr.find("<")) != string::npos) {
        op = "<";
    } else {
        throw runtime_error("无效的不等号");
    }
    
    leftStr = inequalityStr.substr(0, pos);
    rightStr = inequalityStr.substr(pos + op.length());
    
    // 解析左边表达式
    parseExpression(leftStr, ineq.leftCoeff, ineq.leftConst);
    
    // 解析右边表达式
    parseExpression(rightStr, ineq.rightCoeff, ineq.rightConst);
    
    ineq.op = op;
    return ineq;
}

vector<int> InequalitySolver::solveInequality(const Inequality& ineq, int solutionType)
{
    vector<int> solutions;
    
    // 将所有项移到左边：ax + b > 0 形式
    double a = ineq.leftCoeff - ineq.rightCoeff;
    double b = ineq.leftConst - ineq.rightConst;
    
    // 处理a=0的情况
    if (fabs(a) < 1e-10) {
        // 不等式变为 b op 0
        bool condition = false;
        if (ineq.op == ">") condition = (b > 0);
        else if (ineq.op == "<") condition = (b < 0);
        else if (ineq.op == ">=") condition = (b >= 0);
        else if (ineq.op == "<=") condition = (b <= 0);
        else if (ineq.op == "!=") condition = (fabs(b) > 1e-10);
        
        if (!condition) {
            return solutions; // 空解集
        }
        
        // 如果条件成立，根据类型返回所有符合条件的整数
        int start, end;
        if (solutionType == 1) { // 正整数
            start = 1;
            end = 100; // 限制范围
        } else if (solutionType == 2) { // 负整数
            start = -100;
            end = -1;
        } else { // 所有整数
            start = -100;
            end = 100;
        }
        
        for (int x = start; x <= end; x++) {
            solutions.push_back(x);
        }
        return solutions;
    }
    
    // 根据类型确定检查范围
    int start, end;
    if (solutionType == 1) { // 正整数
        start = 1;
        end = 100;
    } else if (solutionType == 2) { // 负整数
        start = -100;
        end = -1;
    } else { // 所有整数
        start = -100;
        end = 100;
    }
    
    // 检查每个整数是否满足不等式
    for (int x = start; x <= end; x++) {
        bool satisfied = false;
        double leftValue = ineq.leftCoeff * x + ineq.leftConst;
        double rightValue = ineq.rightCoeff * x + ineq.rightConst;
        
        if (ineq.op == ">") satisfied = (leftValue > rightValue);
        else if (ineq.op == "<") satisfied = (leftValue < rightValue);
        else if (ineq.op == ">=") satisfied = (leftValue >= rightValue);
        else if (ineq.op == "<=") satisfied = (leftValue <= rightValue);
        else if (ineq.op == "!=") satisfied = (fabs(leftValue - rightValue) > 1e-10);
        
        if (satisfied) {
            solutions.push_back(x);
        }
    }
    
    return solutions;
}

void InequalitySolver::displayResults(const vector<int>& solutions, int solutionType)
{
    resultTable->clearContents();
    resultTable->setRowCount(0);
    
    if (solutions.empty()) {
        resultLabel->setText("解集: 无符合条件的解");
        return;
    }
    
    string typeStr;
    if (solutionType == 1) typeStr = "正整数解";
    else if (solutionType == 2) typeStr = "负整数解";
    else typeStr = "整数解";
    
    resultLabel->setText(QString("解集 (%1): 共 %2 个解").arg(QString::fromStdString(typeStr)).arg(solutions.size()));
    
    resultTable->setRowCount(solutions.size());
    for (size_t i = 0; i < solutions.size(); i++) {
        QTableWidgetItem *indexItem = new QTableWidgetItem(QString::number(i + 1));
        indexItem->setTextAlignment(Qt::AlignCenter);
        resultTable->setItem(i, 0, indexItem);
        
        QTableWidgetItem *valueItem = new QTableWidgetItem(QString::number(solutions[i]));
        valueItem->setTextAlignment(Qt::AlignCenter);
        resultTable->setItem(i, 1, valueItem);
    }
    
    // 调整列宽
    resultTable->resizeColumnsToContents();
}

void InequalitySolver::displayError(const QString& message)
{
    QMessageBox::critical(this, "错误", message);
    statusLabel->setText("错误: " + message.left(50));
}
