" ~/.vim/after/syntax/kivy.vim
"
" Vim syntax file
" Language:	Kivy
" Maintainer:	Gabriel Pettier <gabriel.pettier@gmail.com>
" Last Change:	2020 June 23

syntax clear

syn include @pyth $VIMRUNTIME/syntax/python.vim

syn match kivyComment       /#.*\n/ display contains=pythonTodo,Spell
syn match kivyPreProc       /^\s*#:.*/
syn match kivyRule          /<-*\I\i*\%([,@+]\I\i*\)*>:/
syn match kivyRule          /\[-*\I\i*\%([,@+]\I\i*\)*]:/
syn match kivyRootRule      /^\I\i*:\s*$/

syn region kivyAttrBlock    matchgroup=kivyAttribute start=/^\z(\s\+\)\I\i*\s*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!" contains=@pyth
syn region kivyAttrBlock    matchgroup=kivyAttribute start=/^\s\+\I\i*\s*:\%(\s*\S\)\@=/ end="$" keepend oneline contains=@pyth

syn region kivyId           matchgroup=kivyAttribute start=/^\s\+id\s*:\s*/ end="\w\+\zs" oneline

syn region kivyBindBlock    matchgroup=kivyBind start=/^\z(\s\+\)on_\I\i*\s*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!" contains=@pyth
syn region kivyBindBlock    matchgroup=kivyBind start=/^\s\+on_\i\+\s*:\%(\s*\S\)\@=/ end="$" keepend oneline contains=@pyth

syn region kivyCanvasValue  matchgroup=kivyCanvas start=/^\z(\s\+\)\I\i*\s*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!" contains=@pyth contained
syn region kivyCanvasValue  matchgroup=kivyCanvas start=/^\s\+\I\i*\s*:\%(\s*\S\)\@=/ end="$" keepend oneline contains=@pyth contained
syn region kivyCanvas       matchgroup=kivyCanvas start=/^\z(\s\+\)canvas.*:\s*$/ skip="^\s*$" end="^\%(\z1\s\{4}\)\@!"
                            \   contains=kivyInstruction,kivyPreProc,kivyComment,kivyCanvasValue

syn match kivyInstruction   /^\s\+\u\i*\s*:/ contained
syn match kivyWidget        /^\s\+\u\i*\s*:/

hi def link kivyPreproc     PreProc
hi def link kivyComment     Comment
hi def link kivyRule        Type
hi def link kivyRootRule    Function
hi def link kivyAttribute   Label
hi def link kivyBind        Function
hi def link kivyWidget      Function
hi def link kivyCanvas      special
hi def link kivyInstruction Statement

hi KivyId cterm=underline
hi KivyPreproc cterm=bold

let b:current_syntax = "kivy"
