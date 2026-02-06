# .bashrc
export PS1="\[$(tput bold)\]\[$(tput setaf 6)\]\t \d\n\[$(tput setaf 2)\][\[$(tput setaf 3)\]\u\[$(tput setaf 1)\]@\[$(tput setaf 3)\]\h \[$(tput setaf 6)\]\w\[$(tput setaf 2)\]]\[$(tput setaf 4)\]\\$ \[$(tput sgr0)\]"

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
alias   ls='ls --color --group-directories-first -F'
alias   ll='ls -lah --color --group-directories-first'
alias   tf='tail -f'
alias	log='cd /var/log'
alias   j='joe -nobackups -tab 4 -indentc 32 -istep 2'