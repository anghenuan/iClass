// equation_solver.cpp
#include "equation_solver.h"
#include <QRegularExpression>
#include <QRegularExpressionMatch>

EquationSolver::EquationSolver(QWidget *parent)
    : QMainWindow(parent)
{
    // 设置窗口属性
    setWindowTitle("二元一次方程组求解器");
    setMinimumSize(800, 600);
    
    // 创建中心部件
    centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    // 创建主布局
    mainLayout = new QGridLayout(centralWidget);
    
    // 创建输入部分
    inputGroup = new QGroupBox("输入方程组", centralWidget);
    QGridLayout *inputLayout = new QGridLayout(inputGroup);
    
    eq1Label = new QLabel("方程 1:", inputGroup);
    eq1Input = new QLineEdit(inputGroup);
    eq1Input->setPlaceholderText("例如: 2x + 3y = 5 或 5 = 2x + 3y");
    eq1Input->setMinimumWidth(300);
    
    eq2Label = new QLabel("方程 2:", inputGroup);
    eq2Input = new QLineEdit(inputGroup);
    eq2Input->setPlaceholderText("例如: x - y = 1 或 1 = x - y");
    eq2Input->setMinimumWidth(300);
    
    inputLayout->addWidget(eq1Label, 0, 0);
    inputLayout->addWidget(eq1Input, 0, 1);
    inputLayout->addWidget(eq2Label, 1, 0);
    inputLayout->addWidget(eq2Input, 1, 1);
    
    // 创建按钮部分
    solveButton = new QPushButton("求解方程组", centralWidget);
    clearButton = new QPushButton("清空", centralWidget);
    exampleButton = new QPushButton("示例", centralWidget);
    
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    buttonLayout->addWidget(solveButton);
    buttonLayout->addWidget(clearButton);
    buttonLayout->addWidget(exampleButton);
    buttonLayout->addStretch();
    
    // 创建结果显示部分
    resultGroup = new QGroupBox("求解过程和结果", centralWidget);
    QVBoxLayout *resultLayout = new QVBoxLayout(resultGroup);
    
    resultDisplay = new QTextEdit(resultGroup);
    resultDisplay->setReadOnly(true);
    resultDisplay->setMinimumHeight(300);
    resultLayout->addWidget(resultDisplay);
    
    // 创建状态标签
    statusLabel = new QLabel("请输入两个二元一次方程，然后点击'求解方程组'", centralWidget);
    
    // 将组件添加到主布局
    mainLayout->addWidget(inputGroup, 0, 0);
    mainLayout->addLayout(buttonLayout, 1, 0);
    mainLayout->addWidget(resultGroup, 2, 0);
    mainLayout->addWidget(statusLabel, 3, 0);
    
    // 连接信号和槽
    connect(solveButton, &QPushButton::clicked, this, &EquationSolver::solveEquations);
    connect(clearButton, &QPushButton::clicked, this, &EquationSolver::clearAll);
    connect(exampleButton, &QPushButton::clicked, this, &EquationSolver::showExample);
    
    // 设置样式
    QString style = "QMainWindow { background-color: #f5f5f5; }"
                    "QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 5px; margin-top: 10px; }"
                    "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }"
                    "QPushButton { padding: 8px 16px; font-weight: bold; }"
                    "QTextEdit { background-color: white; border: 1px solid #ccc; }"
                    "QLineEdit { padding: 5px; }";
    setStyleSheet(style);
    
    // 设置示例文本
    eq1Input->setText("2x + 3y = 5");
    eq2Input->setText("x - y = 1");
}

EquationSolver::~EquationSolver()
{
    // Qt对象会自动被删除，因为设置了父对象
}

void EquationSolver::solveEquations()
{
    resultDisplay->clear();
    statusLabel->setText("正在求解...");
    
    // 获取输入
    QString eq1 = eq1Input->text().trimmed();
    QString eq2 = eq2Input->text().trimmed();
    
    if (eq1.isEmpty() || eq2.isEmpty()) {
        displayError("请输入两个方程");
        return;
    }
    
    // 解析方程
    double a1 = 0, b1 = 0, c1 = 0;
    double a2 = 0, b2 = 0, c2 = 0;
    bool isXFirst1 = true, isXFirst2 = true;
    
    if (!parseEquation(eq1, a1, b1, c1, isXFirst1)) {
        displayError("方程1格式错误！\n正确格式示例：2x + 3y = 5 或 5 = 2x + 3y");
        return;
    }
    
    if (!parseEquation(eq2, a2, b2, c2, isXFirst2)) {
        displayError("方程2格式错误！\n正确格式示例：x - y = 1 或 1 = x - y");
        return;
    }
    
    // 显示标准化后的方程
    resultDisplay->append("=== 方程组标准化 ===");
    
    QString eq1Std, eq2Std;
    if (isXFirst1) {
        eq1Std = QString("方程1: %1x + %2y = %3")
                     .arg(formatCoefficient(a1, true))
                     .arg(formatCoefficient(b1))
                     .arg(c1);
    } else {
        eq1Std = QString("方程1: %1y + %2x = %3")
                     .arg(formatCoefficient(b1, true))
                     .arg(formatCoefficient(a1))
                     .arg(c1);
    }
    
    if (isXFirst2) {
        eq2Std = QString("方程2: %1x + %2y = %3")
                     .arg(formatCoefficient(a2, true))
                     .arg(formatCoefficient(b2))
                     .arg(c2);
    } else {
        eq2Std = QString("方程2: %1y + %2x = %3")
                     .arg(formatCoefficient(b2, true))
                     .arg(formatCoefficient(a2))
                     .arg(c2);
    }
    
    resultDisplay->append(eq1Std);
    resultDisplay->append(eq2Std);
    resultDisplay->append("");
    
    // 求解方程组
    solveSystem(a1, b1, c1, a2, b2, c2);
    
    statusLabel->setText("求解完成！");
}

void EquationSolver::solveSystem(double a1, double b1, double c1, double a2, double b2, double c2)
{
    resultDisplay->append("=== 求解过程 ===");
    
    // 显示系数矩阵
    resultDisplay->append("系数矩阵:");
    resultDisplay->append(QString("[ %1  %2 ] [x]   [%3]").arg(a1, 6, 'f', 2).arg(b1, 6, 'f', 2).arg(c1, 6, 'f', 2));
    resultDisplay->append(QString("[ %1  %2 ] [y] = [%3]").arg(a2, 6, 'f', 2).arg(b2, 6, 'f', 2).arg(c2, 6, 'f', 2));
    resultDisplay->append("");
    
    // 计算行列式
    double D = a1 * b2 - a2 * b1;
    double Dx = c1 * b2 - c2 * b1;
    double Dy = a1 * c2 - a2 * c1;
    
    resultDisplay->append("计算行列式:");
    resultDisplay->append(QString("D = a1*b2 - a2*b1 = (%1)*(%2) - (%3)*(%4) = %5")
                          .arg(a1).arg(b2).arg(a2).arg(b1).arg(D));
    resultDisplay->append(QString("Dx = c1*b2 - c2*b1 = (%1)*(%2) - (%3)*(%4) = %5")
                          .arg(c1).arg(b2).arg(c2).arg(b1).arg(Dx));
    resultDisplay->append(QString("Dy = a1*c2 - a2*c1 = (%1)*(%2) - (%3)*(%4) = %5")
                          .arg(a1).arg(c2).arg(a2).arg(c1).arg(Dy));
    resultDisplay->append("");
    
    // 判断解的情况
    if (fabs(D) > 1e-10) {
        // 有唯一解
        double x = Dx / D;
        double y = Dy / D;
        
        resultDisplay->append("=== 求解结果 ===");
        resultDisplay->append(QString("因为 D = %1 ≠ 0，方程组有唯一解:").arg(D));
        resultDisplay->append(QString("x = Dx / D = %1 / %2 = %3").arg(Dx).arg(D).arg(x));
        resultDisplay->append(QString("y = Dy / D = %1 / %2 = %3").arg(Dy).arg(D).arg(y));
        resultDisplay->append("");
        resultDisplay->append(QString("解得: x = %1, y = %2").arg(x).arg(y));
        resultDisplay->append(QString("解为: \n  |x = %1;\n  |y = %2.").arg(x).arg(y));
        
        // 验证解
        resultDisplay->append("");
        resultDisplay->append("=== 验证解 ===");
        double left1 = a1 * x + b1 * y;
        double left2 = a2 * x + b2 * y;
        resultDisplay->append(QString("代入方程1: %1*%2 + %3*%4 = %5 ≈ %6 (右边: %7)")
                              .arg(a1).arg(x).arg(b1).arg(y).arg(left1).arg(c1, 0, 'f', 6).arg(c1));
        resultDisplay->append(QString("代入方程2: %1*%2 + %3*%4 = %5 ≈ %6 (右边: %7)")
                              .arg(a2).arg(x).arg(b2).arg(y).arg(left2).arg(c2, 0, 'f', 6).arg(c2));
        
        if (fabs(left1 - c1) < 0.0001 && fabs(left2 - c2) < 0.0001) {
            resultDisplay->append("验证通过！");
        } else {
            resultDisplay->append("验证失败，可能存在计算误差。");
        }
    } else {
        // D为0的情况
        if (fabs(Dx) < 1e-10 && fabs(Dy) < 1e-10) {
            resultDisplay->append("=== 求解结果 ===");
            resultDisplay->append(QString("因为 D = 0 且 Dx = 0, Dy = 0"));
            resultDisplay->append("方程组有无穷多解（两个方程等价）。");
        } else {
            resultDisplay->append("=== 求解结果 ===");
            resultDisplay->append(QString("因为 D = 0 但 Dx ≠ 0 或 Dy ≠ 0"));
            resultDisplay->append("方程组无解（两个方程矛盾）。");
        }
    }
}

bool EquationSolver::parseEquation(const QString &eqStr, double &a, double &b, double &c, bool &isXFirst)
{
    // 清理输入，移除空格并转换为小写
    QString eq = eqStr.toLower().remove(" ");
    
    if (eq.isEmpty()) return false;
    
    // 检查是否包含等号
    if (!eq.contains("=")) return false;
    
    // 分割等号两边
    QStringList sides = eq.split("=");
    if (sides.size() != 2) return false;
    
    QString left = sides[0];
    QString right = sides[1];
    
    // 默认系数
    double leftX = 0, leftY = 0, leftConst = 0;
    double rightX = 0, rightY = 0, rightConst = 0;
    
    // 解析表达式的函数
    auto parseSide = [](const QString &side, double &coeffX, double &coeffY, double &constant) {
        QString expr = side;
        if (expr.isEmpty()) return true;
        
        // 确保以+或-开头，方便解析
        if (expr[0] != '+' && expr[0] != '-') {
            expr = "+" + expr;
        }
        
        // 使用正则表达式匹配项
        QRegularExpression termRegex("([+-]?\\d*\\.?\\d*)([xy]?)");
        QRegularExpressionMatchIterator i = termRegex.globalMatch(expr);
        
        while (i.hasNext()) {
            QRegularExpressionMatch match = i.next();
            if (match.captured(0).isEmpty()) continue;
            
            QString coeffStr = match.captured(1);
            QString var = match.captured(2);
            
            // 处理系数
            double coeff = 1.0;
            if (!coeffStr.isEmpty() && coeffStr != "+" && coeffStr != "-") {
                coeff = coeffStr.toDouble();
            } else if (coeffStr == "-") {
                coeff = -1.0;
            }
            
            // 分配系数到相应变量
            if (var == "x") {
                coeffX += coeff;
            } else if (var == "y") {
                coeffY += coeff;
            } else {
                constant += coeff;
            }
        }
        
        return true;
    };
    
    // 解析左右两边
    if (!parseSide(left, leftX, leftY, leftConst)) return false;
    if (!parseSide(right, rightX, rightY, rightConst)) return false;
    
    // 将所有项移到左边：左边 - 右边
    a = leftX - rightX;
    b = leftY - rightY;
    c = rightConst - leftConst;  // 常数项移到右边
    
    // 确定x是否在前（系数绝对值较大或默认x在前）
    isXFirst = (fabs(a) >= fabs(b) || (fabs(a) == fabs(b) && a != 0));
    
    return true;
}

QString EquationSolver::formatCoefficient(double coeff, bool isFirst)
{
    if (fabs(coeff) < 1e-10) return "0";  // 处理零
    
    if (isFirst) {
        // 第一个系数
        if (fabs(coeff - 1.0) < 1e-10) return "";
        if (fabs(coeff + 1.0) < 1e-10) return "-";
        return QString::number(coeff);
    } else {
        // 非第一个系数
        if (fabs(coeff - 1.0) < 1e-10) return " + ";
        if (fabs(coeff + 1.0) < 1e-10) return " - ";
        if (coeff > 0) return QString(" + %1").arg(coeff);
        return QString(" - %1").arg(-coeff);
    }
}

void EquationSolver::clearAll()
{
    eq1Input->clear();
    eq2Input->clear();
    resultDisplay->clear();
    statusLabel->setText("已清空所有输入和结果");
}

void EquationSolver::showExample()
{
    eq1Input->setText("3x - 2y = 7");
    eq2Input->setText("x + 4y = 2");
    resultDisplay->clear();
    statusLabel->setText("已加载示例方程组");
}

void EquationSolver::displayError(const QString &message)
{
    QMessageBox::warning(this, "输入错误", message);
    statusLabel->setText("输入错误，请检查方程格式");
}
