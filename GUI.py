from zombie_tests import *
from PyQt5.QtWidgets import *
import os
import sys


class GUI(QWidget):
    def __init__(self):
        # Necessary to use PyQt:
        super().__init__()

        # Elements are added to vertical layout, except for elements added to the embedded child horizontal layouts:
        self.y_layout = QVBoxLayout()                       # Parent (vertical) layout
        self.x_layout = QHBoxLayout()                       # Child (horizontal) layout
        self.x2_layout = QHBoxLayout()                      # 2nd child (horizontal) layout

        # Initial widgets:
        self.intro_label = QLabel("Welcome to the Zombie Killer. I will kill any test that (a) has an 'updated' value "
                                  "that is one week old or older and (b) is still in a running status.")
        self.workspace_prompt = QLabel("What workspace ID do you think has zombies?")
        self.workspace_input = QLineEdit()                  # User inputs workspace ID here
        self.button = QPushButton("Submit")
        self.test_response = QLabel()                       # ZombieTests will return initial output here

        # Instantiate the UI
        self.create_ui()
        self.setWindowTitle("BZM Zombie Killer 2.0")

    def create_ui(self):
        # This function creates the initial UI which will always appear at launch by taking the widgets from __init__()
        # and adding them to the layouts while also determining what the submit button does
        self.button.clicked.connect(lambda: self.submit())  # Clicking "submit" calls submit() function

        # With the layouts defined, add widgets to each layout:
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

        # This group of new labels will now be created:
        master_ids = QLabel()
        masters_w_session_ids = QLabel()
        orphan_session_ids = QLabel()
        total_zombies = QLabel()

        # GUI will now expand and show new information, a new prompt, and new buttons:
        master_ids.setText("This many zombies counted by Master ID: " + str(test.total_zombie_masters))
        masters_w_session_ids.setText("And those Master IDs include this many Session IDs: " +
                                          str(test.total_zombie_sessions))
        orphan_session_ids.setText("But these many zombies with Session IDs have no Master IDs associated: " +
                                       str(test.total_zombie_orphans))
        total_zombies.setText(str(test.total_zombies) + " zombies in total.")
        continue_prompt = QLabel("Shall I kill all these zombies?")

        # Point of no return before killing zombies:
        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(lambda: self.yes(test))  # Clicking calls yes() function
        no_button = QPushButton("No")
        no_button.clicked.connect(self.restart)             # Cancel and restart application by calling restart()

        # Remove the widgets associated with requesting Workspace ID, now that we have it:
        self.intro_label.deleteLater()
        self.workspace_prompt.deleteLater()
        self.workspace_input.deleteLater()
        self.button.deleteLater()

        # Add the new widgets, expanding parent vertical layout:
        self.y_layout.addWidget(master_ids)
        self.y_layout.addWidget(masters_w_session_ids)
        self.y_layout.addWidget(orphan_session_ids)
        self.y_layout.addWidget(total_zombies)
        self.y_layout.addWidget(continue_prompt)

        # Need the new buttons side-by-side, so added a 2nd horizontal layout to appear at the bottom:
        self.x2_layout.addWidget(yes_button)
        self.x2_layout.addWidget(no_button)

        # Add 2nd child layout to parent layout:
        self.y_layout.addLayout(self.x2_layout)

    def yes(self, test):
        # This function calls ZombieTests() kill_zombies() to perform the final tasks of killing all reported zombies
        test.kill_zombies()

        # Results of kill_zombies()
        killed = QLabel()
        immortal_mstrs = QLabel()
        immortal_sessns = QLabel()

        # If master and/or orphan sessions killed, add display of counts to the UI, else do not appear:
        if test.immortal_masters > 0:
            immortal_mstrs.setText(str(test.immortal_masters) + " masters could not be killed.")
            self.y_layout.addWidget(immortal_mstrs)
        if test.immortal_orphans > 0:
            immortal_sessns.setText(str(test.immortal_orphans) + " orphan sessions could not be killed.")
            self.y_layout.addWidget(immortal_sessns)

        # Always display how many total zombies were killed:
        killed.setText(str(test.kill_count) + " zombies killed!")
        self.y_layout.addWidget(killed)

    def restart(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
        # exit(2)


# Start UI
if __name__ == '__main__':
    window = QApplication(sys.argv)
    ui = GUI()
    sys.exit(window.exec_())
