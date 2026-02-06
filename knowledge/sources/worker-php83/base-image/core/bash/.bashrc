# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

alias worker='cd /usr/local/etc/services/GearmanWorker';

export EDITOR='vim'