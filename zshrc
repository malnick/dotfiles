export AZURE_CLIENT_SECRET=vTCY5xA/OQCuONY0sORvMrlvgEDpcXJtEbZszMCo4+g=
export AZURE_CLIENT_ID=7f86a131-a91f-4144-95d7-e7e5824d1df7
export AZURE_SUBSCRIPTION_ID=
export AZURE_TENANT_ID=67a5a29c-8ed9-495f-b559-61288e6cfa14

### Replace ssh-agent with gpg-agent
start_gpg_agent () {
    # You do not need to fork (the &), but better to be safe
    gpg-agent --daemon --enable-ssh-support &
}
# Ensure the GPG agent has started before exporting the SSH_AUTH_SOCK
connect_gpg_agent () {
    gpg-connect-agent /bye;
}

killall gpg-agent;
killall ssh-agent;
start_gpg_agent
connect_gpg_agent
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket);
###

source $HOME/.cargo/env

alias tfm=terraform

alias dcos-prod="DCOS_CONFIG=/home/malnick/.dcos-production/dcos.toml dcos"
alias dcos-quality="DCOS_CONFIG=/home/malnick/.dcos-quality/dcos.toml dcos"


alias ss=gnome-screenshot
# Tap to click 
# xinput set-prop 12 "libinput Tapping Enabled" 1

# pyenv
export PATH="/home/malnick/.pyenv/bin:/home/malnick/.local/bin:$PATH"

# Sticky
alias es="vi ~/sticky.markdown"
alias ss="cat ~/sticky.markdown"

# Remap caps
# setxkbmap -option caps:ctrl_modifier

alias cpt=cryptorious
# Go yo
export GOPATH=/home/malnick/projects/go
export GOROOT=/usr/local/go
export PATH=$PATH:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/local/go/bin:/opt/X11/bin:/usr/local/packer:$GOPATH/bin:/usr/local/heroku/bin

# easy git
alias gcbp='git checkout -b production'
alias gaa='git add .'
# my favorite alias
alias fuckit='puppet apply -e'

# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh
eval "$(hub alias -s)"
# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="gitster"

# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Set to this to use case-sensitive completion
# CASE_SENSITIVE="true"

# Uncomment this to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment to change how often before auto-updates occur? (in days)
# export UPDATE_ZSH_DAYS=13

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want to disable command autocorrection
# DISABLE_CORRECTION="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
# COMPLETION_WAITING_DOTS="true"

# Uncomment following line if you want to disable marking untracked files under
# VCS as dirty. This makes repository status check for large repositories much,
# much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment following line if you want to  shown in the command execution time stamp 
# in the history command output. The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|
# yyyy-mm-dd
# HIST_STAMPS="mm/dd/yyyy"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(git)

source $ZSH/oh-my-zsh.sh

# User configuration


# export MANPATH="/usr/local/man:$MANPATH"

# # Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# ssh
# export SSH_KEY_PATH="~/.ssh/dsa_id"

#export JAVA_HOME=$(/usr/libexec/java_home)
#export EC2_HOME=/usr/local/ec2/ec2-api-tools-1.7.3.0  
#export PATH=$PATH:$EC2_HOME/bin

#alias lg = git log --graph --abbrev-commit --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold cyan)%aD%C(reset) %C(bold green)(%ar)%C(reset)%C(bold yellow)%d%C(reset)%n''          %C(white)%s%C(reset) %C(dim white)- %an%C(reset)' --all

