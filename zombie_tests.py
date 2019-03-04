import sys
import requests
import logging
import time
import load_api_key
import re
from PyQt5.QtWidgets import *


# This is taken from Travis's bulk_processes.py
now = time.time()
base_url = 'https://a.blazemeter.com/api/v4/'
# logging.basicConfig(filename='zombie_tests_%s.log' % now, format='%(asctime)s - %(levelname)s - %(message)s',
#                     level=logging.DEBUG)
auth = load_api_key.get_api_key()


class GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.y_layout = QVBoxLayout()                       # Parent (vertical) layout
        self.x_layout = QHBoxLayout()                       # Child (horizontal) layout
        self.x2_layout = QHBoxLayout()                      # 2nd child (horizontal) layout

        self.intro_label = QLabel("Welcome to the Zombie Killer. I will kill any test that (a) has an 'updated' value "
                                  "that is one week old or older and (b) is still in a running status.")
        self.workspace_prompt = QLabel("What workspace ID do you think has zombies?")
        self.workspace_input = QLineEdit()
        self.button = QPushButton("Submit")
        self.button.clicked.connect(self.get_workspace)
        self.test_response = QLabel("Standing by...")

        self.master_ids = QLabel("Master count standing by...")
        self.masters_w_session_ids = QLabel("Sessions count standing by...")
        self.orphan_session_ids = QLabel("Orphan sessions count standing by...")
        self.total_zombies = QLabel("Total calculation standing by...")

        self.continue_prompt = QLabel("Shall I kill all these zombies?")
        self.yes_button = QPushButton("Yes")                # Pass our zombie lists to the next function.
        self.yes_button.clicked.connect(self.kill_zombies)
        self.no_button = QPushButton("No")
        self.no_button.clicked.connect(self.exit)
        self.goodbye = QLabel("Very well then.  Goodbye.")

        self.killed = QLabel("Kill count standing by...")
        self.immortal_mstrs = QLabel("Immortal masters cou nt standing by...")
        self.immortal_sessns = QLabel("Immortal orphan sessions count standing by...")

        # These three variables store already-parsed JSON response data as Python arrays.
        self.my_zombie_masters = []  # To be killed by Master ID.
        self.my_zombie_sessions = []  # To be ignored; will be killed by Master ID.
        self.my_zombie_orphan_sessions = []  # To be killed by Session ID.

        self.create_ui()
        self.setWindowTitle("BZM Zombie Killer 2.0")

    def create_ui(self):
        self.y_layout.addWidget(self.intro_label)
        self.y_layout.addLayout(self.x_layout)                # child x_layout is nested within parent y_layout

        self.x_layout.addWidget(self.workspace_prompt)
        self.x_layout.addWidget(self.workspace_input)
        self.x_layout.addWidget(self.button)

        self.setLayout(self.y_layout)
        self.show()

    def get_workspace(self):
        # get_workspace modified from Travis's bulk_processes.py
        # This function determines which workspace will be checked for zombies.

        # logging.debug("Function get_workspace")
        workspace_id = self.workspace_input.text()
        trim_workspace_id = workspace_id.replace(' ', '')           # remove spaces from user input, if any
        # logging.debug('Workspace ID: %s', trim_workspace_id)

        if trim_workspace_id.isdigit():                             # verify user actually entered a number
            self.get_active_sessions(trim_workspace_id)             # pass workspace choice on to the next function

        else:
            validated_output = "You did not input a valid number!"
            self.test_response.setText(validated_output)
            self.y_layout.addWidget(self.test_response)

    def get_active_sessions(self, trim_workspace_id):
        # This function finds all tests currently running in the workspace chosen.

        # logging.debug("Function get_active_sessions")
        # logging.info('GET ' + base_url + 'sessions?limit=300&active=true&workspaceId=' + workspace_id)

        # perform a GET and save response to 'r':
        r = requests.get(base_url + 'sessions?limit=300&active=true&workspaceId=' + trim_workspace_id, auth=auth)

        # parse contents of 'r' as JSON then assign to 'response':
        response = r.json()
        if r.status_code == 200:  # verify 'r' contains a status_code of 200 or exit
            validated_output = "Time to kill some zombies for ID # " + trim_workspace_id + "!"
            self.y_layout.addWidget(self.test_response)
            self.test_response.setText(validated_output)
            # logging.debug(response)
            self.find_zombies(response)  # 200 verified, so now pass response into next function

        else:
            # logging.error(response)
            validated_output = "My API call failed. Check log for details. You have been eaten by a zombie."
            self.test_response.setText(validated_output)

    def find_zombies(self, response):
        # This function reviews all running tests and figures out which ones are zombies (last updated 1 week ago or
        # older) We should kill by Master ID if there is one, and be aware that one Master ID can include many Session
        # IDs. Some Session IDs may not have Master IDs. These must be killed by Session ID instead. Don't kill Session
        # IDs belonging to Master IDs since we're already killing them by Master ID.

        # logging.debug("Function find_zombies")

        # Take our running tests and identify which have an 'updated' value that is one week in age or older -- zombies!
        for result in response['result']:
            updated = result['updated']
            if 'masterId' in result:  # Let's figure out which ones have a Master ID.
                if (now - updated) > 604800:
                    my_zom_session = {result['id']}
                    self.my_zombie_sessions.append(my_zom_session)  # Session IDs with matching Master IDs.
                    my_zom_master = {result['masterId']}
                    self.my_zombie_masters.append(my_zom_master)
            else:  # What's left over has a Session ID, but no Master ID.
                if (now - updated) > 604800:
                    my_zom_orphan = {result['id']}
                    self.my_zombie_orphan_sessions.append(my_zom_orphan)

        total_zombie_masters = len(self.my_zombie_masters)
        total_zombie_sessions = len(self.my_zombie_sessions)
        total_zombie_orphans = len(self.my_zombie_orphan_sessions)

        # Our total must count Master IDs and add ONLY those Session IDs not associated with Master IDs.
        total_zombies = len(self.my_zombie_masters) + len(self.my_zombie_orphan_sessions)

        self.master_ids.setText("This many zombies counted by Master ID: " + str(total_zombie_masters))
        self.masters_w_session_ids.setText("And those Master IDs include this many Session IDs: " +
                                           str(total_zombie_sessions))
        self.orphan_session_ids.setText("But these many zombies with Session IDs have no Master IDs associated: " +
                                        str(total_zombie_orphans))
        self.total_zombies.setText(str(total_zombies) + " zombies in total.")

        self.y_layout.addWidget(self.master_ids)
        self.y_layout.addWidget(self.masters_w_session_ids)
        self.y_layout.addWidget(self.orphan_session_ids)
        self.y_layout.addWidget(self.total_zombies)
        # The final prompt before the point of no return:
        self.y_layout.addWidget(self.continue_prompt)
        self.x2_layout.addWidget(self.yes_button)
        self.x2_layout.addWidget(self.no_button)

        self.y_layout.addLayout(self.x2_layout)
        self.setLayout(self.x2_layout)

    def kill_zombies(self):
        # This function takes our lists of zombies and kills each zombie one at a time.
        # Along the way, we'll remove quotes '' and brackets {} leftover from JSON formatting so we can plug IDs into
        # APIs.

        # logging.debug("Function kill_zombies")

        # Kill zombies with Master IDs:
        i = 0
        kill_count = 0
        immortal_masters = 0
        immortal_orphans = 0
        while i < len(self.my_zombie_masters):
            # logging.info('POST ' + base_url + 'masters/' + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) +
            #             '/terminate')
            mr = requests.post(base_url + 'masters/' + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) +
                               '/terminate', auth=auth)
            # masters_response = mr.json()
            while mr.status_code == 202:
                # logging.debug(masters_response)
                kill_count += 1
                # print("Master ID " + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) + " killed!")
            else:
                # logging.error(masters_response)
                immortal_masters += 1
                print("Couldn't kill Master ID " + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) +
                      ".  See logs for details.")
            i += 1

        # Kill sessions without Master IDs:
        i = 0
        while i < len(self.my_zombie_orphan_sessions):
            # logging.info('POST ' + base_url + 'sessions/' + re.sub('[\{\}\']+', '',
            # str(my_zombie_orphan_sessions[i])) + '/terminate')
            sr = requests.post(base_url + 'sessions/' + re.sub('[\{\}\']+', '', str(self.my_zombie_orphan_sessions[i]))
                               + '/terminate', auth=auth)
            sessions_response = sr.json()
            if sr.status_code == 202:
                # logging.debug(sessions_response)
                kill_count += 1
                # print("Session ID " + re.sub('[\{\}\']+', '', str(self.my_zombie_orphan_sessions[i])) + " killed!")
            else:
                # logging.error(sessions_response)
                immortal_orphans += 1
                print("Couldn't kill Session ID " + re.sub('[\{\}\']+', '', str(self.my_zombie_orphan_sessions[i])) +
                      ".  See logs for details.")
            i += 1

        if immortal_masters > 0:
            self.immortal_mstrs.setText(str(immortal_masters) + " masters could not be killed.")
            self.y_layout.addWidget(self.immortal_mstrs)
        if immortal_orphans > 0:
            self.immortal_sessns.setText(str(immortal_orphans) + " orphan sessions could not be killed.")
            self.y_layout.addWidget(self.immortal_sessns)
        self.killed.setText(str(kill_count) + " zombies killed!")
        self.y_layout.addWidget(self.killed)

    def exit(self):
        self.y_layout.addWidget(self.goodbye)
        exit(2)


if __name__ == '__main__':
    window = QApplication(sys.argv)
    ui = GUI()
    sys.exit(window.exec_())
