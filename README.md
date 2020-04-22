Tool for managing custom commands from a central location.

## Installation

The setup is not in its final form.
The current setup procedure is to download the git repository and create a sym-link.

```bash
git clone https://github.com/vaclavblazej/command.git
ln -s ./command/cmd.py ~/bin/cmd
```

## Basic usage

Use `cmd --save` to catalogue a command.

```bash
$ lsb_release -a
Distributor ID:	Ubuntu
Description:	Ubuntu 19.10
Release:	19.10
Codename:	eoan

$ cmd --save
The command to be saved: lsb_release -a   % note that this was pre-filled from history
Short description: Shows the system version
```

Use `cmd --find` to invoke search for commands.

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
Description:	Ubuntu 19.10
Release:	19.10
Codename:	eoan
```

To edit the commands or their description, edit the `./<script_location>/commands.json` file.

## Advanced usage

