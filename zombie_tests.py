import requests
import logging
import time
import load_api_key
import re

# This is taken from Travis's bulk_processes.py
now = time.time()
base_url = 'https://a.blazemeter.com/api/v4/'
logging.basicConfig(filename='zombie_tests_%s.log' % now, format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
auth = load_api_key.get_api_key()


def get_workspace():
    # get_workspace modified from Travis's bulk_processes.py
    # This function determines which workspace will be checked for zombies.
    logging.debug("Function get_workspace")
    print("\nWelcome to the Zombie Killer. I will kill any test that (a) has an 'updated' value that is one week old "
          "or older and (b) is still in a running status.\n")
    workspace_id = input("\nWhat workspace ID do you think has zombies? ")
    workspace_id = workspace_id.replace(' ', '')         # remove spaces from user input, if any
    logging.debug('Workspace ID: %s', workspace_id)
    if workspace_id.isdigit():                           # verify user actually entered a number
        get_active_sessions(workspace_id)                # pass workspace choice on to the next function
    else:
        print("You did not input a valid number!")


def get_active_sessions(workspace_id):
    # This function finds all tests currently running in the workspace chosen.
    logging.debug("Function get_active_sessions")
    logging.info('GET ' + base_url + 'sessions?limit=300&active=true&workspaceId=' + workspace_id)
    # perform a GET and save response to 'r':
    r = requests.get(base_url + 'sessions?limit=300&active=true&workspaceId=' + workspace_id, auth=auth)
    # parse contents of 'r' as JSON then assign to 'response':
    response = r.json()
    if r.status_code == 200:                              # verify 'r' contains a status_code of 200 or exit
        logging.debug(response)
        find_zombies(response)                            # 200 verified, so now pass response into next function
    else:
        logging.error(response)
        print("\nMy API call failed. Check log for details.")
        exit(1)                                           # Set exit code to 1 and terminate cuz your API call failed!


def find_zombies(response):
    # This function reviews all running tests and figures out which ones are zombies (last updated 1 week ago or older)
    # We should kill by Master ID if there is one, and be aware that one Master ID can include many Session IDs.
    # Some Session IDs may not have Master IDs. These must be killed by Session ID instead.
    # Don't kill Session IDs belonging to Master IDs since we're already killing them by Master ID.
    logging.debug("Function find_zombies")
    # These three variables store already-parsed JSON response data as Python arrays.
    my_zombie_masters = []                                # To be killed by Master ID.
    my_zombie_sessions = []                               # To be ignored; will be killed by Master ID.
    my_zombie_orphan_sessions = []                        # To be killed by Session ID.

    # Take our running tests and identify which have an 'updated' value that is one week in age or older -- zombies!
    for result in response['result']:
        updated = result['updated']
        if 'masterId' in result:                           # Let's figure out which ones have a Master ID.
            if (now - updated) > 604800:
                my_zom_session = {result['id']}
                my_zombie_sessions.append(my_zom_session)  # Session IDs with matching Master IDs.
                my_zom_master = {result['masterId']}
                my_zombie_masters.append(my_zom_master)
        else:                                              # What's left over has a Session ID, but no Master ID.
            if (now - updated) > 604800:
                my_zom_orphan = {result['id']}
                my_zombie_orphan_sessions.append(my_zom_orphan)

    # Our total must count Master IDs and add ONLY those Session IDs not associated with Master IDs.
    total_zombies = len(my_zombie_masters) + len(my_zombie_orphan_sessions)

    print("\nHere's our zombies by Master ID:\n")
    print(my_zombie_masters)
    print("\nAnd those Master IDs include these Session IDs:\n")
    print(my_zombie_sessions)
    print("\nBut these zombies with Session IDs have no Master IDs associated:\n")
    print(my_zombie_orphan_sessions)
    print("\nThere are " + str(total_zombies) + " zombies in total.\n")

    # The final prompt before the point of no return.
    choice = input("\nShall I kill all these zombies? (Yes/No)\n")

    if choice == "Yes" or choice == "yes":
        kill_zombies(my_zombie_masters, my_zombie_orphan_sessions)      # Pass our zombie lists to the next function.
    elif choice == "No" or choice == "no":
        print("\nVery well then.  Goodbye.\n")
        exit(2)
    else:
        print("\nThat wasn't a yes or no. Game over, please play again.\n")
        exit(1)


def kill_zombies(my_zombie_masters, my_zombie_orphan_sessions):
    # This function takes our lists of zombies and kills each zombie one at a time.
    # Along the way, we'll remove quotes '' and brackets {} leftover from JSON formatting so we can plug IDs into APIs.
    logging.debug("Function kill_zombies")

    # Kill zombies with Master IDs:
    i = 0
    while i < len(my_zombie_masters):
        logging.info('POST ' + base_url + 'masters/' + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) +
                     '/terminate')
        mr = requests.post(base_url + 'masters/' + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) +
                           '/terminate', auth=auth)
        masters_response = mr.json()
        if mr.status_code == 202:
            logging.debug(masters_response)
            print("Master ID " + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) + " killed!")
        else:
            logging.error(masters_response)
            print("Couldn't kill Master ID " + re.sub('[\{\}]+', '', str(my_zombie_masters[i])) +
                  ".  See logs for details.")
        i += 1

    # Kill sessions without Master IDs:
    i = 0
    while i < len(my_zombie_orphan_sessions):
        logging.info('POST ' + base_url + 'sessions/' + re.sub('[\{\}\']+', '', str(my_zombie_orphan_sessions[i])) +
                     '/terminate')
        sr = requests.post(base_url + 'sessions/' + re.sub('[\{\}\']+', '', str(my_zombie_orphan_sessions[i])) +
                           '/terminate', auth=auth)
        sessions_response = sr.json()
        if sr.status_code == 202:
            logging.debug(sessions_response)
            print("Session ID " + re.sub('[\{\}\']+', '', str(my_zombie_orphan_sessions[i])) + " killed!")
        else:
            logging.error(sessions_response)
            print("Couldn't kill Session ID " + re.sub('[\{\}\']+', '', str(my_zombie_orphan_sessions[i])) +
                  ".  See logs for details.")
        i += 1


get_workspace()     # Start the program by kicking off the first function.
