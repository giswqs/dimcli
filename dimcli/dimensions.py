import configparser
import requests
import os.path
import time
import json
import click
import IPython.display
from itertools import islice

#
#
# File-based Authentication
# ===================
#
# Authentication details can be stored in a `dsl.ini` file in `~/.dimensions/`
# File contents need to have this structure:
#
#
# [instance.live]
# url=https://app.dimensions.ai
# login=your_username
# password=your_password
#
#
# The section name has to start with "instance.". 
# "live" is the default name for most installations.
#
# If you have access to other Dimensions APIs just add an entry for them with a suitable name.
#
#
#


USER_DIR = os.path.expanduser("~/.dimensions/")
USER_CONFIG_FILE = os.path.expanduser(USER_DIR + "dsl.ini")
USER_JSON_OUTPUTS_DIR = os.path.expanduser(USER_DIR + "json/")
USER_HISTORY_FILE = os.path.expanduser(USER_DIR + "history.txt")


class Result(IPython.display.JSON):
    """
    Wrapper for JSON results from DSL

    >>> res = dsl.query("search publications return publications")
    >>> res.data # => shows the underlying JSON data

    # Magic methods: 

    >>> res[publications] # => the dict section
    >>> res.publications # => same
    >>> res.xxx # => false, not found
    >>> res.stats # => the _stats dict

    """
    def __init__(self, data):
        IPython.display.JSON.__init__(self, data)

    def __getitem__(self, key):
        "return dict key as slice"
        if key in self.data:
            return self.data[key]
        else:
            return False

    def __getattr__(self, name):
        if name == "stats":
            name = "_stats" # syntactic sugar
        return self.__getitem__(name)

    def keys(self,):
        return list(self.data.keys())
    def keys_and_count(self,):
        return [(x, len(self.data[x])) for x in self.data.keys()]

class Dsl:
    """
    Object for abstracting common interaction steps with the Dimensions API. 
    Most often you just want to instantiate, autheticate and query() - yeah!

    >>> import dimcli
    # if you have set up a credentials file, no need to pass log in details
    >>> dsl = dimcli.Dsl()
    # queries always return a Result object (subclassing IPython.display.JSON)
    >>> dsl.query("search grants for \"malaria\" return researchers")
    >>> <dimcli.dimensions.Result object>
    # use the .data method to get the JSON
    >>> dsl.query("search grants for \"malaria\" return researchers").data
    >>> {'researchers': [{'id': 'ur.01332073522.49',
            'count': 75,
            'last_name': 'White',
            'first_name': 'Nicholas J'},
        "... JSON data continues ... "

    """
    def __init__(self, instance="live", user="", password="", endpoint="https://app.dimensions.ai"):

        if user and password:
            self._url = endpoint
            self._username = user
            self._password = password
        else:
            config_section = self._get_config_from_file(instance)
            self._url = config_section['url']
            self._username = config_section['login']
            self._password = config_section['password']

        self._login()

    def _get_config_from_file(self, instance_name):
        config = configparser.ConfigParser()
        try:
            config.read(os.path.expanduser(USER_CONFIG_FILE))
        except:
            click.secho("ERROR: Credentials file not found at: %s" % os.path.expanduser(USER_CONFIG_FILE), fg="red")
            click.secho("HowTo: https://github.com/lambdamusic/dimcli#credentials-file", fg="red")
            raise
        try:
            section = config['instance.' + instance_name]
        except:
            click.secho("ERROR: Credentials file does contain settings for instance: %s" % instance_name, fg="red")
            click.secho("HowTo: https://github.com/lambdamusic/dimcli#credentials-file", fg="red")
            raise
        return section

    def _login(self):
        login = {'username': self._username, 'password': self._password}
        response = requests.post(
            '{}/api/auth.json'.format(self._url), json=login)
        response.raise_for_status()

        token = response.json()['token']
        self._headers = {'Authorization': "JWT " + token}

    def query(self, q, retry=0):
        """
        Execute DSL query.
        By default it doesn't show results, but it uses the iPython rich widgets for it, optimized for Jupyter Notebooks.
        """
        #   Execute DSL query.
        response = requests.post(
            '{}/api/dsl.json'.format(self._url), data=q, headers=self._headers)
        if response.status_code == 429:  
            # Too Many Requests
            print(
                'Too Many Requests for the Server. Sleeping for 30 seconds and then retrying.'
            )
            time.sleep(30)
            return self.query(q)
        elif response.status_code == 403:  
            # Forbidden:
            print('Login token expired. Logging in again.')
            self._login()
            return self.query(q)
        elif response.status_code in [200, 400, 500]:  
            ###  
            # OK or Error Info :-)
            ###
            result = Result(response.json())
            return result
        else:
            if retry > 0:
                print('Retrying in 30 secs')
                time.sleep(30)
                return self.query(
                    q,
                    retry=retry - 1)
            else:
                response.raise_for_status()


def chunks_of(data, size):
    it = iter(data)
    chunk = list(islice(it, size))
    while chunk:
        yield chunk
        chunk = list(islice(it, size))
