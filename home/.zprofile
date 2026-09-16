
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

# Setting PATH for Python 3.13
# The original version is saved in .zprofile.pysave
if [ "$(uname -s)" = Darwin ]; then
  PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:${PATH}"
fi
export PATH
