#!/usr/bin/env python3
# git-user.py
# GusE 2015.04.29 V0.1
"""
Allows you to save multiple user profiles and set them as project defaults
"""

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
__version__ = "0.1"
__maintainer__ = "Gus Esquivel"
__email__ = "gesquive@gmail"
__status__ = "Beta"

verbose = False
debug = False

app = os.path.basename(sys.argv[0])
app = 'git user' if app == 'git-user' else app

#TODO: Get parser working in python 2.7
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     add_help=False)

    # parser.add_argument('--action', default='get', help=argparse.SUPPRESS)
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

    delete_parser = subparsers.add_parser('delete', aliases=['del'], help='Delete a profile')
    delete_parser.add_argument('--action', default='del', help=argparse.SUPPRESS)
    delete_parser.add_argument('profile_name', help='The profile to delete')

    set_parser = subparsers.add_parser('set', help='Set the profile for the current project')
    set_parser.add_argument('--action', default='set', help=argparse.SUPPRESS)
    set_parser.add_argument('--global', '-g', action='store_true',
                            default=False, dest='use_global',
                            help='Apply the profile too the global config')
    set_parser.add_argument('profile_name', help='The profile to set')

    remove_parser = subparsers.add_parser('remove', aliases=['unset'],
                                          help='Remove the profile from the current project')
    remove_parser.add_argument('--action', default='remove', help=argparse.SUPPRESS)
    remove_parser.add_argument('--global', '-g', action='store_true',
                               default=False, dest='use_global',
                               help='Remove the user from the global config')

    # parser.add_argument('--default', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--path', '-p', default='.',
                        help='The project to set/get the user')
    parser.add_argument("-c", "--config-file", default='~/.git_profiles',
                       help="The path to the config file "
                       "(default:~/.git_profiles")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                       help="Writes all messages to console.")
    parser.add_argument("-h", "--help", action="help",
                       help="Show this help message and exit.")
    parser.add_argument("-V", "--version", action="version",
                       version="{} v{}\n".format(__app__, __version__))
    parser.add_argument("-D", "--debug", action="store_true", dest="debug",
                       help=argparse.SUPPRESS)

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
    # print(args)
    init_logging(args.verbose, args.debug)
    colors.init()

# git user set <nickname>
# git user remove
# git user add <nickname> <user_name> <user_email>
# git user edit <nickname> <user_name> <user_email>
# git user del <nickname>
# git user list
    try:
        user_file = UserFile(args.config_file)
        if 'action' not in args or args.action == 'list':
            print('Current Project:')
            project_path = os.path.abspath(args.path)
            print("  Path: {}".format(colors.green(project_path)))

            user_info = get_global_user(all=True)
            nav = colors.red('N/A')
            name = user_info['name'] if 'name' in user_info else nav
            email = user_info['email'] if 'email' in user_info else nav
            print("  User: {} <{}>".format(colors.green(name), colors.blue(email)))

            profiles = user_file.get_all_profiles()
            if len(profiles.keys()) == 0:
                logging.info('There are no profiles in your config.')
                logging.info('  Add a profile with '
                             '"{} add <profile> <name> <email>"'.format(app))
                logging.info('Type "{} --help" for more info.'.format(app))
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


def get_global_user(all=False):
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
    #TODO: Make it so the default userfile path is in the global gitconfig
    def __init__(self, path):
        self.path = os.path.expanduser(path)
        self._config = configparser.ConfigParser()
        self._config.read(self.path)

    def check_profile(self, profile):
        return profile in self._config.section()

    def add_profile(self, profile, name, email):
        self._config[profile] = {}
        self._config[profile]['name'] = name
        self._config[profile]['email'] = email
        self._write()

    edit_profile = add_profile

    def remove_profile(self, profile):
        self._config.remove_section(profile)
        self._write()

    def get_profile(self, profile):
        if profile in self._config:
            return self._config[profile]
        return None

    def get_all_profiles(self):
        all = {}
        for profile in self._config.sections():
            all[profile] = {
                'name': self._config[profile]['name'],
                'email': self._config[profile]['email']
            }
        return all

    def _write(self):
        with open(self.path, 'w') as configfile:
            self._config.write(configfile)


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
