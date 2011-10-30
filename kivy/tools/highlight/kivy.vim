" Vim syntax file
" Language:	Kivy
" Maintainer:	George Sebastian <11george.s@gmail.com>
" Last Change:	2011 May 1

" For version 5.x: Clear all syntax items.
" For version 6.x: Quit when a syntax file was already loaded.
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn match kivyPreProc       /#:.*/
syn match kivyComment       /#.*/
syn match kivyRule          /<\I\i*\(,\s*\I\i*\)*>:/
syn match kivyAttribute     /\<\I\i*\>/ nextgroup=kivyValue

syn include @pyth $VIMRUNTIME/syntax/python.vim
syn region kivyValue start=":" end=/$/  contains=@pyth skipwhite

syn region kivyAttribute matchgroup=kivyIdent start=/[\a_][\a\d_]*:/ end=/$/ contains=@pyth skipwhite

if version >= 508 || !exists("did_python_syn_inits")
  if version <= 508
    let did_python_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

    HiLink kivyPreproc      PreProc
    HiLink kivyComment      Comment
    HiLink kivyRule         Function
    HiLink kivyIdent        Statement
    HiLink kivyAttribute    Label
  delcommand HiLink
endif
