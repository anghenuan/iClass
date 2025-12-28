// equation_solver.h
#ifndef EQUATION_SOLVER_H
#define EQUATION_SOLVER_H

#include <QMainWindow>
#include <QWidget>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QTextEdit>
#include <QGroupBox>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QMessageBox>
#include <cmath>

class EquationSolver : public QMainWindow
{
    Q_OBJECT

public:
    EquationSolver(QWidget *parent = nullptr);
    ~EquationSolver();

private slots:
    void solveEquations();
    void clearAll();
    void showExample();

private:
    // 界面组件
    QWidget *centralWidget;
    QGridLayout *mainLayout;
    
    // 输入部分
    QGroupBox *inputGroup;
    QLabel *eq1Label, *eq2Label;
    QLineEdit *eq1Input, *eq2Input;
    
    // 按钮部分
    QPushButton *solveButton;
    QPushButton *clearButton;
    QPushButton *exampleButton;
    
    // 结果显示部分
    QGroupBox *resultGroup;
    QTextEdit *resultDisplay;
    
    // 底部状态
    QLabel *statusLabel;
    
    // 核心求解函数
    bool parseEquation(const QString &eqStr, double &a, double &b, double &c, bool &isXFirst);
    void solveSystem(double a1, double b1, double c1, double a2, double b2, double c2);
    
    // 辅助函数
    QString formatCoefficient(double coeff, bool isFirst = false);
    void displayError(const QString &message);
};

#endif // EQUATION_SOLVER_H
