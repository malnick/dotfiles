if has('python3')
  command! VimPilotChat call VimPilotOpenChat()

  function! VimPilotOpenChat() abort
    python3 << EOF
import sys
import os
sys.path.append(os.path.expanduser('~/.vim/vim-pilot/python'))
from vim_pilot import open_chat
open_chat()
EOF
  endfunction
else
  echoerr 'VimPilot requires +python3 support.'
endif 