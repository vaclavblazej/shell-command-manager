Tool for managing custom commands from a central location.

## Installation

The setup is not in its final form.
The current setup procedure is to download the git repository and create a sym-link.

```bash
git clone https://github.com/vaclavblazej/command.git
ln -s ./command/cmd.py ~/bin/cmd
```

## Basic usage

Use `cmd -s` (or `cmd --save`) to catalogue a command.

```bash
$ lsb_release -a
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04 LTS
Release:	20.04
Codename:	focal

$ cmd --save
The command to be saved: lsb_release -a   % note that this was pre-filled from history
Short description: Shows the system version
```

Use `cmd -f` (or `cmd --find`) to invoke search for commands.

```bash
$ cmd --find
========================================
query $ system                            % items matching the regex are displayed
--- 1 ------------------------------
cmd: do-release-upgrade
des: Upgrades the system to the newest released version
--- 2 ------------------------------
cmd: lsb_release -a
des: Shows the system version
========================================
query $ 2                                 % choose the command by entering its number
run command: lsb_release -a
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04 LTS
Release:	20.04
Codename:	focal
```

To edit the commands or their description, edit the `./<script_location>/commands.json` file.

### Completion

You can setup completion by adding `source ./<script_location>/completion/setup.bash` or `setup.zsh` depending on your shell `rc` script.

```bash
echo "source \"$PWD/command/completion/setup.bash\"" >> ~/.bashrc
```

```zsh
echo "source \"$PWD/command/completion/setup.zsh\"" >> ~/.zshrc
```

## Advanced usage

We manage custom scripts, their help, and completion.

* execution
* help
* completion

One function for all three because they have too much in common.
Flags used to determine what we want to return.

All three variants are delegated lower (into arguments) and in the lowest level, we return (or do) the wanted result.
In execution, we perform the task.
In help and completion, we set the result into the relevant location.

### Execution

The custom script should be an executable file.

### Help

Help is invoked by calling `script --help <arguments>` where arguments are in the precise form as they would have been without the `--help` argument.
It prints a string to standard output which describes what our current command does, and if there are any expected arguments.

### Completion

Completion is invoked by calling `script --complete <arguments>` and prints out the list of words which are sensible arguments in the next places.
The last argument is considered as *argument prefix* and is used to filter out possible words.
If no filtering is wanted, the last argument should be empty-string.



