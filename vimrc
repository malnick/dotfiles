let g:terraform_align=1
let g:terraform_fmt_on_save=1

set nocursorcolumn
syntax sync minlines=256
set re=1

execute pathogen#infect()
syntax on
filetype plugin indent on

let g:airline_powerline_fonts = 1
let g:airline_theme = 'dark'

set signcolumn=yes
let g:gitgutter_highlight_lines = 1
let g:gitgutter_enabled = 1 
let g:gitgutter_signs = 1
let g:gitgutter_realtime = 1
let g:gitgutter_eager = 1

autocmd BufWritePre *.py :%s/\s\+$//e

set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 1 
let g:syntastic_enable_highlighting = 1
let g:syntastic_ruby_checkers = ['rubocop', 'mri', 'jruby']
let g:syntastic_go_checkers = ['go', 'errcheck']
let g:syntastic_aggregate_errors = 1

" configure pylint to disable certain annoying messages
" http://pylint-messages.wikidot.com/all-codes
let g:syntastic_python_pylint_args="-d C0103,C0111,R0201"

" vim-go
let g:go_highlight_functions = 1
let g:go_highlight_methods = 1
let g:go_highlight_fields = 1
let g:go_highlight_types = 1
let g:go_highlight_operators = 1

let g:go_fmt_command = "goimports"
"let g:go_metalinter_autosave = 1
let g:go_metalinter_autosave_enabled = ['errcheck']
"let g:go_metalinter_enabled = ['errcheck', 'golint', 'govet']

syntax enable
let g:solarized_termtrans = 1
set background=dark
colorscheme solarized

au BufRead *.markdown setlocal spell 
set ruler
filetype plugin on
set shell=zsh
set cursorline
set clipboard=unnamed

set tabstop=2
set shiftwidth=2
set smarttab
set expandtab
set softtabstop=4
set autoindent
set paste

let g:rustfmt_autosave = 1
