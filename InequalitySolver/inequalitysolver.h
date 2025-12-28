#ifndef INEQUALITYSOLVER_H
#define INEQUALITYSOLVER_H

#include <QMainWindow>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QComboBox>
#include <QPushButton>
#include <QTextEdit>
#include <QTableWidget>
#include <QGroupBox>
#include <QHeaderView>
#include <QMessageBox>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <sstream>

using namespace std;

// 用于存储不等式的结构体
struct Inequality {
    double leftCoeff;     // 左边x的系数
    double leftConst;     // 左边的常数项
    double rightCoeff;    // 右边x的系数
    double rightConst;    // 右边的常数项
    string op;           // 不等号
};

class InequalitySolver : public QMainWindow
{
    Q_OBJECT

public:
    InequalitySolver(QWidget *parent = nullptr);
    ~InequalitySolver();

private slots:
    void solveClicked();
    void clearClicked();
    void exampleClicked();
    void helpClicked();

private:
    void setupUI();
    void parseExpression(const string& expr, double& coeff, double& constant);
    Inequality parseInequality(const string& inequalityStr);
    vector<int> solveInequality(const Inequality& ineq, int solutionType);
    void displayResults(const vector<int>& solutions, int solutionType);
    void displayError(const QString& message);

    // UI组件
    QWidget *centralWidget;
    QVBoxLayout *mainLayout;
    
    // 输入区域
    QGroupBox *inputGroup;
    QLabel *inequalityLabel;
    QLineEdit *inequalityInput;
    QLabel *exampleLabel;
    
    // 求解类型区域
    QGroupBox *typeGroup;
    QLabel *typeLabel;
    QComboBox *typeComboBox;
    
    // 按钮区域
    QGroupBox *buttonGroup;
    QPushButton *solveButton;
    QPushButton *clearButton;
    QPushButton *exampleButton;
    QPushButton *helpButton;
    
    // 结果显示区域
    QGroupBox *resultGroup;
    QLabel *resultLabel;
    QTableWidget *resultTable;
    QTextEdit *standardFormDisplay;
    
    // 状态标签
    QLabel *statusLabel;
};

#endif // INEQUALITYSOLVER_H
