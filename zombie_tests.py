import requests
# import logging
import time
import load_api_key
import re


class ZombieTests:
    # The following are class variables which the GUI() class will interact with anytime it instantiates this class.
    # Variables 'now' through 'auth' were taken from Travis's bulk_processes.py script:
    now = time.time()
    base_url = 'https://a.blazemeter.com/api/v4/'
    # logging.basicConfig(filename='zombie_tests_%s.log' % now, format='%(asctime)s - %(levelname)s - %(message)s',
    #                     level=logging.DEBUG)
    auth = load_api_key.get_api_key()

    # These variables will return initial feedback to the user via the UI in GUI()
    valid = 0
    validated_output = "NO OUTPUT"

    # These three variables store already-parsed JSON response data as Python arrays:
    my_zombie_masters = []                                      # To be killed by Master ID.
    my_zombie_sessions = []                                     # To be ignored; will be killed by Master ID.
    my_zombie_orphan_sessions = []                              # To be killed by Session ID.

    # These variables store counts of their namesake variables:
    total_zombie_masters = 0
    total_zombie_sessions = 0
    total_zombie_orphans = 0

    # These variables tallie up all zombies killed and all that somehow survived
    kill_count = 0
    immortal_masters = 0
    immortal_orphans = 0

    # Our total must count Master IDs and add ONLY those Session IDs not associated with Master IDs.
    total_zombies = 0

    def get_workspace(self, workspace_id):
        # get_workspace modified from Travis's bulk_processes.py
        # This function determines which workspace will be checked for zombies.

        # logging.debug("Function get_workspace")

        workspace_id = workspace_id.replace(' ', '')            # remove spaces from user input, if any
        # logging.debug('Workspace ID: %s', trim_workspace_id)

        if workspace_id.isdigit():                              # verify user actually entered a number
            self.get_active_sessions(workspace_id)              # pass workspace choice on to next function

        else:
            self.valid = 0
            self.validated_output = "You did not input a valid number!"

    def get_active_sessions(self, workspace_id):
        # This function finds all tests currently running in the workspace chosen.

        # logging.debug("Function get_active_sessions")
        # logging.info('GET ' + base_url + 'sessions?limit=300&active=true&workspaceId=' + workspace_id)

        # perform a GET and save response to 'r':
        r = requests.get(self.base_url + 'sessions?limit=300&active=true&workspaceId=' + workspace_id, auth=self.auth)

        # parse contents of 'r' as JSON then assign to 'response':
        response = r.json()

        # Verify 'r' contains a status_code of 200 or exit
        if r.status_code == 200:
            self.valid = 1
            self.validated_output = "Time to kill some zombies for ID # " + workspace_id + "!"
            # logging.debug(response)
            self.find_zombies(response)                         # 200 verified, so now pass response into next function
        else:
            # logging.error(response)
            self.valid = 0
            self.validated_output = "My API call failed. Check log for details. You have been eaten by a zombie."

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
                if (self.now - updated) > 604800:
                    my_zom_session = {result['id']}
                    self.my_zombie_sessions.append(my_zom_session)  # Session IDs with matching Master IDs.
                    my_zom_master = {result['masterId']}
                    self.my_zombie_masters.append(my_zom_master)
            else:  # What's left over has a Session ID, but no Master ID.
                if (self.now - updated) > 604800:
                    my_zom_orphan = {result['id']}
                    self.my_zombie_orphan_sessions.append(my_zom_orphan)

        # These variables store counts of their namesake variables:
        self.total_zombie_masters = len(self.my_zombie_masters)
        self.total_zombie_sessions = len(self.my_zombie_sessions)
        self.total_zombie_orphans = len(self.my_zombie_orphan_sessions)

        # Our total must count Master IDs and add ONLY those Session IDs not associated with Master IDs.
        self.total_zombies = len(self.my_zombie_masters) + len(self.my_zombie_orphan_sessions)

    def kill_zombies(self):
        # This function takes our lists of zombies and kills each zombie one at a time. Along the way, we'll remove
        # quotes '' and brackets {} leftover from JSON formatting so we can plug IDs into APIs.

        # logging.debug("Function kill_zombies")

        # Kill zombies with Master IDs:
        i = 0
        while i < self.total_zombie_masters:
            # logging.info('POST ' + base_url + 'masters/' + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) +
            #             '/terminate')
            mr = requests.post(self.base_url + 'masters/' + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) +
                               '/terminate', auth=self.auth)
            # masters_response = mr.json()
            while mr.status_code == 202:
                # logging.debug(masters_response)
                self.kill_count += 1
                # print("Master ID " + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) + " killed!")
            else:
                # logging.error(masters_response)
                self.immortal_masters += 1
                print("Couldn't kill Master ID " + re.sub('[\{\}]+', '', str(self.my_zombie_masters[i])) +
                      ".  See logs for details.")
            i += 1

        # Kill sessions without Master IDs:
        i = 0
        while i < self.total_zombie_orphans:
            # logging.info('POST ' + base_url + 'sessions/' + re.sub('[\{\}\']+', '',
            # str(my_zombie_orphan_sessions[i])) + '/terminate')
            sr = requests.post(self.base_url + 'sessions/' + re.sub('[\{\}\']+', '',
                                                                    str(self.my_zombie_orphan_sessions[i])) +
                               '/terminate', auth=self.auth)
            sessions_response = sr.json()
            if sr.status_code == 202:
                # logging.debug(sessions_response)
                self.kill_count += 1
                # print("Session ID " + re.sub('[\{\}\']+', '', str(self.my_zombie_orphan_sessions[i])) + " killed!")
            else:
                # logging.error(sessions_response)
                self.immortal_orphans += 1
                print("Couldn't kill Session ID " + re.sub('[\{\}\']+', '', str(self.my_zombie_orphan_sessions[i])) +
                      ".  See logs for details.")
            i += 1

