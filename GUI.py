from zombie_tests import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import sys


class GUI(QWidget):
    def __init__(self):
        # Necessary to use PyQt:
        super().__init__()

        # Elements are added to vertical layout, except for elements added to the embedded child horizontal layouts:
        self.y_layout = QVBoxLayout()                       # Parent (vertical) layout
        self.y_layout.setAlignment(Qt.AlignCenter)
        self.y_layout.setSizeConstraint(QLayout.SetFixedSize)   # Layout will resize as widgets are added/removed
        self.x_layout = QHBoxLayout()                       # Child (horizontal) layout
        self.x_layout.setAlignment(Qt.AlignCenter)
        self.x2_layout = QHBoxLayout()                      # 2nd child (horizontal) layout
        self.x2_layout.setAlignment(Qt.AlignCenter)

        # Initial widgets:
        self.intro_label = QLabel("Welcome to the Zombie Killer. I will kill any test that (a) has an 'updated' value "
                                  "that is one week old or older and (b) is still in a running status.")
        self.workspace_prompt = QLabel("What workspace ID do you think has zombies?")
        self.workspace_input = QLineEdit()                  # User inputs workspace ID here
        self.button = QPushButton("Submit")
        self.button.setMaximumWidth(100)
        self.test_response = QLabel()                       # ZombieTests will return initial output here

        # This group of new labels & buttons will be added when zombie_results() is called:
        self.master_ids = QLabel()
        self.masters_w_session_ids = QLabel()
        self.orphan_session_ids = QLabel()
        self.total_zombies = QLabel()
        self.continue_prompt = QLabel("Shall I kill all these zombies?")
        self.continue_prompt.setAlignment(Qt.AlignCenter)
        self.yes_button = QPushButton("Yes")
        self.yes_button.setMaximumWidth(100)
        self.no_button = QPushButton("No")
        self.no_button.setMaximumWidth(100)
        self.exit_before_button = QPushButton("Exit")
        self.exit_before_button.setMaximumWidth(100)

        # Instantiate the UI
        self.create_ui()
        self.setWindowTitle("BZM Zombie Killer 2.0")

    def create_ui(self):
        # This function creates the initial UI which will always appear at launch by taking the widgets from __init__()
        # and adding them to the layouts while also determining what the submit button does
        logo_label = QLabel(self)
        logo_label.setAlignment(Qt.AlignCenter)
        logo = QPixmap('logo.png')
        logo_label.setPixmap(logo)

        self.button.clicked.connect(lambda: self.submit())  # Clicking "submit" calls submit() function

        # With the layouts defined, add widgets to each layout:
        self.y_layout.addWidget(logo_label)
        self.y_layout.addWidget(self.intro_label)
        self.y_layout.addLayout(self.x_layout)              # Child x_layout is nested within parent y_layout
        self.y_layout.addWidget(self.test_response)

        # This horizontal layout is embedded within the vertical layout:
        self.x_layout.addWidget(self.workspace_prompt)
        self.x_layout.addWidget(self.workspace_input)
        self.x_layout.addWidget(self.button)

        # Add the horizontal layout to the vertical layout:
        self.setLayout(self.y_layout)

        # Make UI actually visible:
        self.show()

        # Note: Additional layouts/widgets will be added by later functions, but this function creates the initial UI
        # that will always be seen by the user.

    def submit(self):
        # Clicking the submit button calls this function, which launches the first function of ZombieTests()
        test = ZombieTests()                                # Instantiate new ZombieTests() object to use its functions
        test.get_workspace(self.workspace_input.text())     # Calls get_workspace() from ZombieTests

        self.test_response.setText(test.validated_output)   # ZombieTests() tells us if we can proceed or not

        if test.valid == 1:                                 # Else do nothing; warning message alerts user
            self.zombie_results(test)                       # Calls zombie_results()

    def zombie_results(self, test):
        # This function takes the test results determined from ZombieTests() find_zombies() (kicked off by earlier by
        # submit()) and informs the user about the zombies available to kill, as well as giving the user the option to
        # continue on to actually killing them or not (as a safeguard against accidental terminations).

        # GUI will now expand and show new information, a new prompt, and new buttons:
        self.master_ids.setText("This many zombies counted by Master ID: " + str(test.total_zombie_masters))
        self.masters_w_session_ids.setText("And those Master IDs include this many Session IDs: " +
                                          str(test.total_zombie_sessions))
        self.orphan_session_ids.setText("But these many zombies with Session IDs have no Master IDs associated: " +
                                       str(test.total_zombie_orphans))
        self.total_zombies.setText(str(test.total_zombies) + " zombies in total.")

        # Point of no return before killing zombies:
        self.yes_button.clicked.connect(lambda: self.yes(test))  # Clicking calls yes() function
        self.no_button.clicked.connect(self.restart)             # Cancel and restart application by calling restart()
        self.exit_before_button.clicked.connect(lambda: self.exit())    # Clicking calls exit() function to quit

        # Remove the widgets associated with requesting Workspace ID, now that we have it:
        self.intro_label.deleteLater()
        self.workspace_prompt.deleteLater()
        self.workspace_input.deleteLater()
        self.button.deleteLater()

        # Add the new widgets, expanding parent vertical layout:
        self.y_layout.addWidget(self.master_ids)
        self.y_layout.addWidget(self.masters_w_session_ids)
        self.y_layout.addWidget(self.orphan_session_ids)
        self.y_layout.addWidget(self.total_zombies)
        self.y_layout.addWidget(self.continue_prompt)

        # Need the new buttons side-by-side, so added a 2nd horizontal layout to appear at the bottom:
        self.x2_layout.addWidget(self.yes_button)
        self.x2_layout.addWidget(self.no_button)
        self.x2_layout.addWidget(self.exit_before_button)

        # Add 2nd child layout to parent layout:
        self.y_layout.addLayout(self.x2_layout)

    def yes(self, test):
        # This function calls ZombieTests() kill_zombies() to perform the final tasks of killing all reported zombies
        test.kill_zombies()

        # Results of kill_zombies()
        killed = QLabel()
        immortal_mstrs = QLabel()
        immortal_sessns = QLabel()

        exit_after_button = QPushButton("Exit")
        exit_after_button.setMaximumWidth(100)
        exit_after_button.clicked.connect(lambda: self.exit())  # Clicking calls exit() function to quit

        restart_button = QPushButton("Restart")
        restart_button.setMaximumWidth(100)
        restart_button.clicked.connect(lambda: self.restart())

        x3_layout = QHBoxLayout()
        x3_layout.setAlignment(Qt.AlignCenter)

        # If master and/or orphan sessions killed, add display of counts to the UI, else do not appear:
        if test.immortal_masters > 0:
            immortal_mstrs.setText(str(test.immortal_masters) + " masters could not be killed.")
            self.y_layout.addWidget(immortal_mstrs)
        if test.immortal_orphans > 0:
            immortal_sessns.setText(str(test.immortal_orphans) + " orphan sessions could not be killed.")
            self.y_layout.addWidget(immortal_sessns)

        # Remove previous labels & buttons since no longer needed:
        self.test_response.deleteLater()
        self.master_ids.deleteLater()
        self.masters_w_session_ids.deleteLater()
        self.orphan_session_ids.deleteLater()
        self.total_zombies.deleteLater()
        self.continue_prompt.deleteLater()
        self.yes_button.deleteLater()
        self.no_button.deleteLater()
        self.exit_before_button.deleteLater()
        self.x_layout.deleteLater()
        self.x2_layout.deleteLater()

        # Always display how many total zombies were killed:
        killed.setText(str(test.kill_count) + " zombies killed!")
        self.y_layout.addWidget(killed)
        x3_layout.addWidget(restart_button)
        x3_layout.addWidget(exit_after_button)

        self.y_layout.addLayout(x3_layout)

    def restart(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def exit(self):
        exit(2)


# Start UI
if __name__ == '__main__':
    window = QApplication(sys.argv)
    ui = GUI()
    sys.exit(window.exec_())
