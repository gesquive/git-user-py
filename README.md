##git-user

Git plugin that allows you to save multiple user profiles and set them as project defaults

```
usage: git-user.py [--path PATH] [-c CONFIG_FILE] [-v] [-h] [-V]
                   {list,add,edit,del,set,rem} ...

positional arguments:
  {list,add,edit,del,set,rem}
                        commands
    list                List all the saved profiles
    add                 Add a new profile
    edit                Edit a new profile
    del                 Delete a profile
    set                 Set the profile for the current project
    rem                 Remove the profile from the current project

optional arguments:
  --path PATH, -p PATH  The project to set/get the user
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        The path to the config file (default:~/.git_profiles)
  -v, --verbose         Writes all messages to console.
  -h, --help            Show this help message and exit.
  -V, --version         show program's version number and exit
```

### Installation Instructions

Run the following command:
```
SDIR=/usr/local/bin/; wget https://raw.github.com/gesquive/git-user/master/git-user.py -O ${SDIR}/git-user && chmod +x ${SDIR}/git-user
```

If you wish to install to a different directory just change the `SDIR` value.
Keep in mind, if you want to be able to run the script as a git sub-command (ie. run as `git substatus`) you must make the script executable and available on the `$PATH`

### TODO
 - Show a status printout in case script is called within a git directory
 - Add auto-detection of a color tty and adjust printout accordingly