# Cisco Auto Release

Automatically releases messages that get into Cisco's useless Spam Quarantine.

## Setup
> I do not know how crontab works on windows. This instruction is for Mac OS/Linux.

If you have access to `data.cs.purdue.edu`, you can install this script there. 

1. Install python 3 (it is preinstalled on `data`)
2. `pip3 install requests`
3. `mkdir -p ~/scripts/cisco/ && cd ~/scripts/cisco/ && wget https://raw.githubusercontent.com/elnardu/cisco_auto_release/master/cisco_auto_release.py`
4. `chmod +x ~/scripts/cisco/cisco_auto_release.py`
5. `~/scripts/cisco/cisco_auto_release.py`
   * Follow the instructions on screen
   * If you had any emails in the quarantine, you should receive them now
6. `crontab -e`
7. Add `*/5 * * * * ~/scripts/cisco/cisco_auto_release.py` after the comments and save the file
   * This will run the script every 5 minutes
