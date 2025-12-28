#include "inequalitysolver.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    
    // 设置应用程序样式
    app.setStyle("Fusion");
    
    // 创建主窗口
    InequalitySolver window;
    
    // 设置窗口图标
    window.setWindowIcon(QIcon(":/icon.ico")); // 如果有图标的话
    
    // 显示窗口
    window.show();
    
    return app.exec();
}
