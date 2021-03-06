#!/usr/bin/env python2
# TODO: Fix stylesheets for lineedits.
# setMinimumSize (something is setting this. unset it)
# Store buttons in variables.

from math import factorial
import sys

from PyQt4 import QtGui, QtCore

from calculation import evaluate


class SelectAllLineEdit(QtGui.QLineEdit):
    "Overloaded QLineEdit to select all text when clicked into."

    def mousePressEvent (self, e):
        self.selectAll()


class GUICalculator(QtGui.QWidget):

    def __init__(self):
        super(GUICalculator, self).__init__()
        self.setGeometry(500, 300, 350, 300)
        self.setWindowTitle("Calculator")
        self.setWindowIcon(QtGui.QIcon("calculator.png"))

        self.mrc = None  # Memory recall variable.
        edits = self.create_edit_layout()
        grid = self.create_button_layout()

        mainlayout = QtGui.QVBoxLayout()
        mainlayout.addLayout(edits)
        mainlayout.addLayout(grid)

        self.setLayout(mainlayout)

    def create_button_layout(self):
        "Creates the grid of calculator buttons."

        labels = ["exit", "mrc", "m+", "m-",
                  "clear", "(", ")", "!",
                  "sqrt", "pow", "%", "/",
                  "7", "8", "9", "*",
                  "4", "5", "6", "-",
                  "1", "2", "3", "+",
                  "0", ".", "c", "="]

        buttons = {i: QtGui.QPushButton(i) for i in labels}

        for b in buttons.values():
            b.clicked.connect(self.button_clicked)

        # Create our positions grid (0,0), (0,1) etc.
        pos = [(i, j) for i in range(7) for j in range(4)]

        layout = QtGui.QGridLayout()

        for i in range(len(labels)):
            layout.addWidget(buttons[labels[i]], pos[i][0], pos[i][1])

        return layout

    def create_edit_layout(self):

        self.in_edit = QtGui.QLineEdit()
        self.in_edit.setStyleSheet("padding: 0px;")
        self.in_edit.returnPressed.connect(self.update_output)
        self.out_edit = SelectAllLineEdit()
        self.out_edit.setStyleSheet("padding: 0px;")
        self.out_edit.setReadOnly(True)

        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self.in_edit)
        layout.addWidget(self.out_edit)

        return layout

    def button_clicked(self):
        text = str(self.sender().text())
        if text in "0123456789.-+/%()**":
            self.in_edit.setText(self.in_edit.text() + text)
        elif text == "=":
            self.update_output()
        elif text == "exit":
            sys.exit()
        elif text == "c":
            self.in_edit.setText(self.in_edit.text()[:-1])
        elif text == "clear":
            self.in_edit.setText("")
        elif text == "!":
            factor = str(factorial(int(self.in_edit.text())))
            self.out_edit.setText(factor)
            self.in_edit.setText("")
        elif text == "sqrt":
            self.in_edit.setText("({})**0.5".format(self.in_edit.text()))
            self.update_output()
        elif text == "pow":
            self.in_edit.setText(self.in_edit.text() + "**")
        elif text == "mrc":
            self.mrc = str(self.in_edit.text())
        elif text == "m+":
            self.in_edit.setText(self.in_edit.text() + self.mrc)
        elif text == "m-":
            t = str(self.in_edit.text())
            if self.mrc in t:
                length = len(self.mrc)
                idx = t.rfind(self.mrc)
                self.in_edit.setText(t[:idx] + t[idx + length:])

    def update_output(self):
        output = evaluate(str(self.in_edit.text()))
        if output:
            self.out_edit.setText(str(output))
            self.in_edit.setText("")

def main():
    app = QtGui.QApplication(sys.argv)
    c = GUICalculator()
    c.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
