let s:root = fnamemodify(expand('<sfile>:p'), ':h:h')
execute 'set runtimepath^=' . fnameescape(s:root)
set t_Co=256
colorscheme apollo

call assert_equal('apollo', g:colors_name)
call assert_equal('dark', &background)
call assert_equal('#cfbc97', tolower(synIDattr(hlID('Normal'), 'fg', 'gui')))
call assert_equal('#141617', tolower(synIDattr(hlID('Normal'), 'bg', 'gui')))
call assert_equal('180', synIDattr(hlID('Normal'), 'fg', 'cterm'))
call assert_equal('233', synIDattr(hlID('Normal'), 'bg', 'cterm'))
call assert_equal('#fabd2f', tolower(synIDattr(hlID('CursorLineNr'), 'fg', 'gui')))
call assert_equal('#b8bb26', tolower(synIDattr(hlID('String'), 'fg', 'gui')))
call assert_equal('#fb4934', tolower(synIDattr(hlID('DiagnosticError'), 'fg', 'gui')))
call assert_equal('#83a598', tolower(synIDattr(hlID('DiagnosticInfo'), 'fg', 'gui')))
call assert_equal([
      \ '#1d2021', '#fb4934', '#b8bb26', '#fabd2f',
      \ '#83a598', '#d3869b', '#8ec07c', '#d5c4a1',
      \ '#665c54', '#fb4934', '#b8bb26', '#fabd2f',
      \ '#83a598', '#d3869b', '#8ec07c', '#fbf1c7',
      \ ], g:terminal_ansi_colors)
call assert_equal('#1d2021', g:terminal_color_0)
call assert_equal('#fbf1c7', g:terminal_color_15)

if len(v:errors)
  for s:error in v:errors
    echomsg s:error
  endfor
  cquit
endif
quitall!
