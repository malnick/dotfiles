" Load the isolated legacy VimPilot Python dependency when installed.
if has('python3') && filereadable(expand('~/.local/share/dotfiles/vimpilot-site.txt'))
python3 << EOF
import os, site
with open(os.path.expanduser('~/.local/share/dotfiles/vimpilot-site.txt')) as f:
    site.addsitedir(f.read().strip())
EOF
endif
execute pathogen#infect()
syntax on
filetype plugin indent on

set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_aggregate_errors = 1
let g:syntastic_go_checkers = ['govet', 'errcheck', 'go']
let g:go_list_type = "quickfix"
