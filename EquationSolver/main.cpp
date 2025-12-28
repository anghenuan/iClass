// main.cpp
#include "equation_solver.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    EquationSolver solver;
    solver.show();
    return app.exec();
}
