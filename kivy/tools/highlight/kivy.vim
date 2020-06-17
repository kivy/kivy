" ~/.vim/after/syntax/kivy.vim
"
" Vim syntax file
" Language:	Kivy
" Maintainer:	Gabriel Pettier <gabriel.pettier@gmail.com>
" Last Change:	2017 august 26

syntax clear

syn include @pyth $VIMRUNTIME/syntax/python.vim

syn match kivyComment       /#.*\n/ display contains=pythonTodo,Spell
syn match kivyPreProc       /^\s*#:.*/
syn match kivyAttribute     /\I\i*/ nextgroup=kivyValue skipwhite
syn match kivyBind          /on_\I\i*:/
syn match kivyRule          /<-*\I\i*\%([,@+]\I\i*\)*>:/
syn match kivyRule          /\[-*\I\i*\%([,@+]\I\i*\)*]:/
syn match kivyRootRule      /^\I\i*:\s*$/
syn match kivyInstruction   /^\s\+\u\i*:\s*/ contained
syn match kivyWidget        /^\s\+\u\i*:/

syn region kivyBindBlock    start=/^\(\z(\s\+\)\)on_\I\i*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!" contains=@pyth,kivyBind
syn match kivyBindBlock     /on_\i\+:.*$/ contains=@pyth,kivyBind

syn match kivyValue         /:.*$/ contained contains=@pyth

syn match kivyIdLine        /^\s\+id\s*:\s*\w\+\s*/ contains=kivyIdStart
syn match kivyIdStart       /id\s*:/he=s+2 contained nextgroup=kivyId skipwhite
syn match kivyId            /\w\+/ contained

syn region kivyCanvas       start=/^\z(\s\+\)canvas.*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!" contains=kivyInstruction,kivyValue,kivyPreProc,kivyComment

hi def link kivyPreproc     PreProc
hi def link kivyComment     Comment
hi def link kivyRule        Type
hi def link kivyRootRule    Function
hi def link kivyIdStart     kivyAttribute
hi def link kivyAttribute   Label
hi def link kivyBind        Function
hi def link kivyWidget      Function
hi def link kivyCanvas      special
hi def link kivyInstruction Statement

hi KivyId cterm=underline
hi KivyPreproc cterm=bold
