#!/usr/bin/env python
# git-user.py
# GusE 2015.04.29 V0.1
"""
Allows you to save multiple user profiles and set them as project defaults
"""
__version__ = "1.2"

import sys
import os
import argparse
import subprocess
import traceback
import logging
import logging.handlers

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

__app__ = os.path.basename(__file__)
__author__ = "Gus Esquivel"
__copyright__ = "Copyright 2015"
__credits__ = ["Gus Esquivel"]
__license__ = "GPL"
__maintainer__ = "Gus Esquivel"
__email__ = "gesquive@gmail"
__status__ = "Production"

script_www = 'https://github.com/gesquive/git-user'
script_url = 'https://raw.github.com/gesquive/git-user/master/git-user.py'

verbose = False
debug = False

default_profile_path = '~/.git_profiles'

app = os.path.basename(sys.argv[0])
app = 'git user' if app == 'git-user' else app

def parse_args():

    # We need this function for 2.7 compatibility
    # grabbed from: http://stackoverflow.com/a/26379693/613218
    def set_default_subparser(self, name, args=None):
        """default subparser selection. Call after setup, just before parse_args()
        name: is the name of the subparser to call by default
        args: if set is the argument list handed to parse_args()

        tested with 2.7, 3.2, 3.3, 3.4
        it works with 2.6 assuming argparse is installed
        """
        subparser_found = False
        for arg in sys.argv[1:]:
            if arg in ['-h', '--help']:  # global help if no subparser
                break
        else:
            for x in self._subparsers._actions:
                if not isinstance(x, argparse._SubParsersAction):
                    continue
                for sp_name in x._name_parser_map.keys():
                    if sp_name in sys.argv[1:]:
                        subparser_found = True
            if not subparser_found:
                # insert default in first position, this implies no
                # global options without a sub_parsers specified
                if args is None:
                    sys.argv.insert(1, name)
                else:
                    args.insert(0, name)

    argparse.ArgumentParser.set_default_subparser = set_default_subparser

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     add_help=False)

    subparsers = parser.add_subparsers(help='commands')

    list_parser = subparsers.add_parser('list', help='List all the saved profiles')
    list_parser.add_argument('--action', default='list', help=argparse.SUPPRESS)

    add_parser = subparsers.add_parser('add', help='Add a new profile')
    add_parser.add_argument('--action', default='add', help=argparse.SUPPRESS)
    add_parser.add_argument('profile_name', help='The profile name')
    add_parser.add_argument('user_name', help='The user name')
    add_parser.add_argument('user_email', help='The user email')

    edit_parser = subparsers.add_parser('edit', help='Edit a new profile')
    edit_parser.add_argument('--action', default='edit', help=argparse.SUPPRESS)
    edit_parser.add_argument('profile_name', help='The profile name')
    edit_parser.add_argument('user_name', help='The user name')
    edit_parser.add_argument('user_email', help='The user email')

    delete_parser = subparsers.add_parser('del', help='Delete a profile')
    delete_parser.add_argument('--action', default='del', help=argparse.SUPPRESS)
    delete_parser.add_argument('profile_name', help='The profile to delete')

    set_parser = subparsers.add_parser('set', help='Set the profile for the current project')
    set_parser.add_argument('--action', default='set', help=argparse.SUPPRESS)
    set_parser.add_argument('--global', '-g', action='store_true',
                            default=False, dest='use_global',
                            help='Apply the profile too the global config')
    set_parser.add_argument('profile_name', help='The profile to set')

    remove_parser = subparsers.add_parser('rem',
                                          help='Remove the profile from the current project')
    remove_parser.add_argument('--action', default='remove', help=argparse.SUPPRESS)
    remove_parser.add_argument('--global', '-g', action='store_true',
                               default=False, dest='use_global',
                               help='Remove the user from the global config')

    parser.add_argument('--path', '-p', default='.',
                        help='The project to set/get the user')
    parser.add_argument("-c", "--config-file", default=None,
                       help="The path to the config file "
                       "(default:~/.git_profiles")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                       help="Writes all messages to console.")
    parser.add_argument("-h", "--help", action="help",
                       help="Show this help message and exit.")
    parser.add_argument("-V", "--version", action="version",
                       version="{} v{}\n".format(__app__, __version__))
    parser.add_argument("-u", "--update", action="store_true", dest="update",
                        help="Checks server for an update, replaces the current "\
                        "version if there is a newer version available.")
    parser.add_argument("-D", "--debug", action="store_true", dest="debug",
                       help=argparse.SUPPRESS)

    parser.set_default_subparser('list')
    args = parser.parse_args()
    return args


def init_logging(verbose, debug):
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("")
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)

    if verbose or debug:
        logging.getLogger('').setLevel(logging.DEBUG)
        logging.debug("Verbose mode activated.")
    else:
        logging.getLogger('').setLevel(logging.INFO)


def main():
    global verbose, debug

    args = parse_args()
    init_logging(args.verbose, args.debug)
    colors.init()

    if args.update:
        update(script_url)
        sys.exit()

    try:
        user_file = UserFile(args.config_file)
        if 'action' not in args or args.action == 'list':
            project_path = os.path.abspath(args.path)
            user_is_local = project_has_user(project_path)
            if user_is_local:
                print('Project Profile:')
                print('  Path: {}'.format(colors.green(project_path)))
            else:
                print('Global Profile:')
            user_info = get_git_user(all=True)
            nav = colors.red('N/A')
            name = user_info['name'] if 'name' in user_info else nav
            email = user_info['email'] if 'email' in user_info else nav
            print("  User: {} <{}>".format(colors.green(name), colors.blue(email)))
            print('')

            profiles = user_file.get_all_profiles()
            if len(profiles.keys()) == 0:
                logging.info('There are no profiles in your config.')
                logging.info('  Add a profile with '
                             '"{} add <profile> <name> <email>"'.format(app))
                logging.info('Type "{} --help" for more info.'.format(app))
            else:
                print('Saved Profiles:')
                for profile in sorted(profiles):
                    print('  {}: {} <{}>'.format(colors.yellow(profile),
                                 profiles[profile]['name'],
                                 profiles[profile]['email']))
        elif args.action == 'add' or args.action == 'edit':
            user_file.add_profile(args.profile_name, args.user_name,
                args.user_email)
            logging.info('Added profile "{}"'.format(args.profile_name))
        elif args.action == 'del':
            user_file.remove_profile(args.profile_name)
            logging.info('Deleted profile "{}"'.format(args.profile_name))
        elif args.action == 'set':
            profile = user_file.get_profile(args.profile_name)
            if not profile:
                logging.info('There is no profile named "{}" in the config.'.format(args.profile_name))
                logging.info('You can add the profile with:')
                logging.info('  "{} {} add <name> <email>"'.format(app, args.profile_name))
            else:
                project_path = os.path.abspath(args.path)
                if args.use_global:
                    set_global_user(profile['name'], profile['email'])
                    logging.info('The global user has been set too '
                                 '"{} <{}>"'.format(profile['name'], profile['email']))
                else:
                    set_project_user(project_path, profile['name'], profile['email'])
                    logging.info('The user for the "{}" repository has been '
                                 'set too "{} <{}>"'.format(os.path.basename(project_path),
                                    profile['name'], profile['email']))
        elif args.action == 'remove':
            project_path = os.path.abspath(args.path)
            if args.use_global:
                unset_global_user()
                logging.info('Removed user info from the global config')
            else:
                unset_project_user(project_path)
                logging.info('Removed user info from "{}"'.format(os.path.basename(project_path)))

    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(traceback.format_exc())

def shell(command, cwd=None, seperate=True):
    """Returns the stdout from the given command.
    """
    cmd = subprocess.Popen(command, shell=seperate, stdout=subprocess.PIPE,
                           cwd=cwd)
    res = cmd.stdout.read()
    cmd.wait()
    return res

def project_has_user(project_path):
    name = shell('git -C {} config --local user.name'.format(project_path)).\
                decode('ascii').strip()
    return (name != '')

def get_git_user(all=False):
    info = {}
    loc = '' if all else '--global'

    name = shell('git config {} user.name'.format(loc)).decode('ascii').strip()
    if name is not '':
        info['name'] = name

    email = shell('git config {} user.email'.format(loc)).decode('ascii').strip()
    if email is not '':
        info['email'] = email
    return info

def set_project_user(project_path, user, email):
    shell('git -C "{}" config user.name "{}"'.format(project_path, user))
    shell('git -C "{}" config user.email "{}"'.format(project_path, email))

def set_global_user(user, email):
    shell('git config --global user.name "{}"'.format(user))
    shell('git config --global user.email "{}"'.format(email))

def unset_project_user(project_path):
    shell('git -C "{}" config --remove-section user'.format(project_path))

def unset_global_user():
    shell('git config --global --remove-section user'.format(project_path))

class UserFile:
    def __init__(self, path):
        self.path = self._get_config_path(path)
        self._config = configparser.ConfigParser()
        self._config.read(self.path)

    def _get_config_path(self, arg_path):
        if arg_path:
            return os.path.expanduser(arg_path)
        # Try to get the config path from the gitconfig, if it's not there
        #   set it and return
        config_path = shell('git config user.profiles').decode('ascii').strip()
        if len(config_path) == 0:
            default_path = default_profile_path
            shell('git config --global user.profiles {}'.format(default_path))
            config_path = default_path
        return os.path.expanduser(config_path)

    def check_profile(self, profile):
        return profile in self._config.section()

    def add_profile(self, profile, name, email):
        if profile not in self._config.sections():
            self._config.add_section(profile)
        self._config.set(profile, 'name', name)
        self._config.set(profile, 'email', email)
        self._write()

    edit_profile = add_profile

    def remove_profile(self, profile):
        self._config.remove_section(profile)
        self._write()

    def get_profile(self, profile):
        if profile in self._config.sections():
            return {
                'name': self._config.get(profile, 'name'),
                'email': self._config.get(profile, 'email')
            }
        return None

    def get_all_profiles(self):
        all = {}
        for profile in self._config.sections():
            all[profile] = {
                'name': self._config.get(profile, 'name'),
                'email': self._config.get(profile, 'email')
            }
        return all

    def _write(self):
        with open(self.path, 'w') as configfile:
            self._config.write(configfile)



def update(dl_url, force_update=False):
    """
Attempts to download the update url in order to find if an update is needed.
If an update is needed, the current script is backed up and the update is
saved in its place.
"""
    import urllib
    import re
    from subprocess import call
    def compare_versions(vA, vB):
        """
Compares two version number strings
@param vA: first version string to compare
@param vB: second version string to compare
@author <a href="http_stream://sebthom.de/136-comparing-version-numbers-in-jython-pytho/">Sebastian Thomschke</a>
@return negative if vA < vB, zero if vA == vB, positive if vA > vB.
"""
        if vA == vB: return 0

        def num(s):
            if s.isdigit(): return int(s)
            return s

        seqA = map(num, re.findall('\d+|\w+', vA.replace('-SNAPSHOT', '')))
        seqB = map(num, re.findall('\d+|\w+', vB.replace('-SNAPSHOT', '')))

        # this is to ensure that 1.0 == 1.0.0 in cmp(..)
        lenA, lenB = len(seqA), len(seqB)
        for i in range(lenA, lenB): seqA += (0,)
        for i in range(lenB, lenA): seqB += (0,)

        rc = cmp(seqA, seqB)

        if rc == 0:
            if vA.endswith('-SNAPSHOT'): return -1
            if vB.endswith('-SNAPSHOT'): return 1
        return rc

    # dl the first 256 bytes and parse it for version number
    try:
        logging.info("Checking the latest version...")
        http_stream = urllib.urlopen(dl_url)
        update_file = http_stream.read(256)
        http_stream.close()
    except IOError:
        logging.exception("Unable to retrieve version data")
        return

    match_regex = re.search(r'__version__ *= *"(\S+)"', update_file)
    if not match_regex:
        logging.error("No version info could be found")
        return
    update_version = match_regex.group(1)

    if not update_version:
        logging.error("Unable to parse version data")
        return

    if force_update:
        logging.info("Forcing update, downloading version {}..."
                     "".format(update_version))
    else:
        cmp_result = compare_versions(__version__, update_version)
        if cmp_result < 0:
            logging.info("Newer version ({}) available, downloading..."
                         "".format(update_version))
        elif cmp_result > 0:
            logging.info("Local version ({}) is newer then available ({}), "
                         "not updating.".format(__version__, update_version))
            return
        else:
            logging.info("You already have the latest version.")
            return

    # dl, backup, and save the updated script
    app_path = os.path.realpath(sys.argv[0])

    if not os.access(app_path, os.W_OK):
        logging.error("Cannot update -- unable to write to {}".format(app_path))

    dl_path = app_path + ".new"
    backup_path = app_path + ".old"
    try:
        dl_file = open(dl_path, 'w')
        http_stream = urllib.urlopen(dl_url)
        total_size = None
        bytes_so_far = 0
        chunk_size = 8192
        try:
            total_size = int(http_stream.info().getheader('Content-Length').strip())
        except:
            # The header is improper or missing Content-Length, just download
            dl_file.write(http_stream.read())

        while total_size:
            chunk = http_stream.read(chunk_size)
            dl_file.write(chunk)
            bytes_so_far += len(chunk)

            if not chunk:
                break

            percent = float(bytes_so_far) / total_size
            percent = round(percent*100, 2)
            sys.stdout.write("Downloaded {} of {} bytes ({:0.2f})\r"
                             "".format(bytes_so_far, total_size, percent))

            if bytes_so_far >= total_size:
                sys.stdout.write('\n')

        http_stream.close()
        dl_file.close()
    except IOError:
        logging.exception("Download failed")
        return

    try:
        os.rename(app_path, backup_path)
    except OSError:
        logging.exception()("Unable to rename {} to {}: ({}) {}"
                            "".format(app_path, backup_path, errno, strerror))
        return

    try:
        os.rename(dl_path, app_path)
    except OSError:
        logging.exception("Unable to rename {} to {}: ({}) {}"
                          "".format(dl_path, app_path, errno, strerror))
        return

    try:
        import shutil
        shutil.copymode(backup_path, app_path)
    except:
        pass
        os.chmod(app_path, 0o755)

    logging.info("New version installed as {}".format(app_path))
    logging.info("(previous version backed up to {})".format(backup_path))
    return


class colors:
    PRE = ''
    BLUE = ''
    GREEN = ''
    YELLOW = ''
    RED = ''
    END = ''

    @staticmethod
    def init():
        if colors.supports_color():
            colors.PRE = '\033[95m'
            colors.BLUE = '\033[94m'
            colors.GREEN = '\033[92m'
            colors.YELLOW = '\033[93m'
            colors.RED = '\033[91m'
            colors.END = '\033[0m'

    @staticmethod
    def blue(msg):
        return '{}{}{}'.format(colors.BLUE, msg, colors.END)
    @staticmethod
    def green(msg):
        return '{}{}{}'.format(colors.GREEN, msg, colors.END)
    @staticmethod
    def yellow(msg):
        return '{}{}{}'.format(colors.YELLOW, msg, colors.END)
    @staticmethod
    def red(msg):
        return '{}{}{}'.format(colors.RED, msg, colors.END)


    @staticmethod
    def supports_color():
        """
        Returns True if the running system's terminal supports color, and False
        otherwise.
        """
        plat = sys.platform
        supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                      'ANSICON' in os.environ)
        # isatty is not always implemented, #6223.
        is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        if not supported_platform or not is_a_tty:
            return False
        return True


if __name__ == '__main__':
    main()
