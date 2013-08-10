;;; kivy-mode.el --- Emacs major mode for editing Kivy files
;;
;; Author: Dean Serenevy <dean@serenevy.net>
;; Version: 0.1.0
;;
;; This document borrowed heavily from yaml-mode.el by Yoshiki Kurihara and
;; Marshall Vandegrift.
;;
;; This file is not part of Emacs


;; This file is free software; you can redistribute it and/or modify it
;; under the terms of the GNU General Public License as published by the
;; Free Software Foundation; version 3.

;; This file is distributed in the hope that it will be useful, but WITHOUT
;; ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
;; FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
;; more details.

;; You should have received a copy of the GNU General Public License along
;; with GNU Emacs; see the file COPYING. If not, write to the Free Software
;; Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
;; USA.

;;; Installation:

;; To install, just drop this file into a directory in your `load-path' and
;; (optionally) byte-compile it. To automatically handle files ending in
;; '.kv', add something like:
;;
;;    (require 'kivy-mode)
;;    (add-to-list 'auto-mode-alist '("\\.kv$" . kivy-mode))
;;
;; to your .emacs file.
;;
;; Unlike python-mode, this mode follows the Emacs convention of not
;; binding the ENTER key to `newline-and-indent'. To get this behavior, add
;; the key definition to `kivy-mode-hook':
;;
;;    (add-hook 'kivy-mode-hook
;;     '(lambda ()
;;        (define-key kivy-mode-map "\C-m" 'newline-and-indent)))


;; User definable variables

(defgroup kivy nil
  "Support for the kivy user interface definition format"
  :group 'languages
  :prefix "kivy-")

(defcustom kivy-mode-hook nil
  "*Hook run by `kivy-mode'."
  :type 'hook
  :group 'kivy)

(defcustom kivy-indent-offset 4
  "*Amount of offset per level of indentation."
  :type 'integer
  :group 'kivy)

(defcustom kivy-backspace-function 'backward-delete-char-untabify
  "*Function called by `kivy-electric-backspace' when deleting backwards."
  :type 'function
  :group 'kivy)

(defface kivy-tab-face
  '((((class color)) (:background "red" :foreground "red" :bold t))
    (t (:reverse-video t)))
  "Face to use for highlighting tabs in kivy files."
  :group 'faces
  :group 'kivy)

(defcustom kivy-imenu-generic-expression
  '((nil  "^\\([<>a-zA-Z_-]+\\):"          1))
  "The imenu regex to parse an outline of the kivy file."
  :type 'string
  :group 'kivy)


;; Constants

(defconst kivy-mode-version "0.1.0" "Version of `kivy-mode.'")

(defconst kivy-blank-line-re "^ *$"
  "Regexp matching a line containing only (valid) whitespace.")

(defconst kivy-comment-re "\\(?:^\\|\\s-+\\)\\(#.*\\)"
  "Regexp matching a line containing a kivy comment or delimiter.")

(defconst kivy-directive-re "^\\(?:#:\\)\\(\\w+ +.*\\)"
  "Regexp matching a line contatining a kivy directive.")

(defconst kivy-tag-re "^ *id: *\\([^ \n]+\\)$"
  "Rexexp matching a kivy tag.")

(defconst kivy-bare-scalar-re
  "\\(?:[^-:,#!\n{\\[ ]\\|[^#!\n{\\[ ]\\S-\\)[^#\n]*?"
  "Rexexp matching a kivy bare scalar.")

(defconst kivy-hash-key-re
  (concat "^ *"
          "\\(" kivy-bare-scalar-re "\\) *:"
          "\\(?: +\\|$\\)")
  "Regexp matching a single kivy hash key.")

(defconst kivy-nested-map-re
  (concat ".*: *$")
  "Regexp matching a line beginning a kivy nested structure.")

(defconst kivy-constant-scalars-re
  (concat "\\(?:^\\|\\(?::\\|-\\|,\\|{\\|\\[\\) +\\) *"
          (regexp-opt
           '("True" "False" "None") t)
          " *$")
  "Regexp matching certain scalar constants in scalar context")



;; Mode setup

(defvar kivy-mode-map ()
  "Keymap used in `kivy-mode' buffers.")
(if kivy-mode-map
    nil
  (setq kivy-mode-map (make-sparse-keymap))
  (define-key kivy-mode-map [backspace] 'kivy-electric-backspace)
  (define-key kivy-mode-map "\C-c<" 'kivy-indent-shift-left)
  (define-key kivy-mode-map "\C-c>" 'kivy-indent-shift-right)
  )

(defvar kivy-mode-syntax-table nil
  "Syntax table in use in kivy-mode buffers.")
(if kivy-mode-syntax-table
    nil
  (setq kivy-mode-syntax-table (make-syntax-table))
  (modify-syntax-entry ?\' "\"" kivy-mode-syntax-table)
  (modify-syntax-entry ?\" "\"" kivy-mode-syntax-table)
  (modify-syntax-entry ?# "<" kivy-mode-syntax-table)
  (modify-syntax-entry ?\n ">" kivy-mode-syntax-table)
  (modify-syntax-entry ?\\ "\\" kivy-mode-syntax-table)
  (modify-syntax-entry ?- "_" kivy-mode-syntax-table)
  (modify-syntax-entry ?_ "w" kivy-mode-syntax-table)
  )


;;;###autoload
(add-to-list 'auto-mode-alist '("\\.kv$" . kivy-mode))


;;;###autoload
(define-derived-mode kivy-mode fundamental-mode "kivy"
  "Simple mode to edit kivy.

\\{kivy-mode-map}"
  (set (make-local-variable 'comment-start) "# ")
  (set (make-local-variable 'comment-start-skip) "#+ *")
  (set (make-local-variable 'indent-line-function) 'kivy-indent-line)
  (set (make-local-variable 'font-lock-defaults)
       '(kivy-font-lock-keywords
         nil nil nil nil
         (font-lock-syntactic-keywords))))


;; Font-lock support

(defvar kivy-font-lock-keywords
  (list
   (cons kivy-comment-re '(1 font-lock-comment-face))
   (cons kivy-constant-scalars-re '(1 font-lock-constant-face))
   (cons kivy-tag-re '(1 font-lock-function-name-face))
   (cons kivy-hash-key-re '(1 font-lock-variable-name-face t))
   (cons kivy-directive-re '(1 font-lock-builtin-face))
   '("^[\t]+" 0 'kivy-tab-face t))
  "Additional expressions to highlight in kivy mode.")

(defvar kivy-font-lock-syntactic-keywords
  (list '())
  "Additional syntax features to highlight in kivy mode.")


;; Indentation and electric keys

(defun kivy-compute-indentation ()
  "Calculate the maximum sensible indentation for the current line."
  (save-excursion
    (beginning-of-line)
    (forward-line -1)
    (while (and (looking-at kivy-blank-line-re)
                (> (point) (point-min)))
      (forward-line -1))
    (+ (current-indentation)
       (if (looking-at kivy-nested-map-re) kivy-indent-offset 0)
       )))

(defun kivy-indent-line ()
  "Indent the current line.
The first time this command is used, the line will be indented to the
maximum sensible indentation.  Each immediately subsequent usage will
back-dent the line by `kivy-indent-offset' spaces.  On reaching column
0, it will cycle back to the maximum sensible indentation."
  (interactive "*")
  (let ((ci (current-indentation))
        (cc (current-column))
        (need (kivy-compute-indentation)))
    (save-excursion
      (beginning-of-line)
      (delete-horizontal-space)
      (if (and (equal last-command this-command) (/= ci 0))
          (indent-to (* (/ (- ci 1) kivy-indent-offset) kivy-indent-offset))
        (indent-to need)))
    (if (< (current-column) (current-indentation))
        (forward-to-indentation 0))))

(defun kivy-electric-backspace (arg)
  "Delete characters or back-dent the current line.
If invoked following only whitespace on a line, will back-dent to the
immediately previous multiple of `kivy-indent-offset' spaces."
  (interactive "*p")
  (if (or (/= (current-indentation) (current-column)) (bolp))
      (funcall kivy-backspace-function arg)
    (let ((ci (current-column)))
      (beginning-of-line)
      (delete-horizontal-space)
      (indent-to (* (/ (- ci (* arg kivy-indent-offset))
                       kivy-indent-offset)
                    kivy-indent-offset)))))


(defun kivy-set-imenu-generic-expression ()
  (make-local-variable 'imenu-generic-expression)
  (make-local-variable 'imenu-create-index-function)
  (setq imenu-create-index-function 'imenu-default-create-index-function)
  (setq imenu-generic-expression kivy-imenu-generic-expression))

(add-hook 'kivy-mode-hook 'kivy-set-imenu-generic-expression)


(defun kivy-mode-version ()
  "Diplay version of `kivy-mode'."
  (interactive)
  (message "kivy-mode %s" kivy-mode-version)
  kivy-mode-version)

(defun kivy-indent-shift-left (start end &optional count)
  "Shift lines contained in region START END by COUNT columns to the left.
COUNT defaults to `kivy-indent-offset'.  If region isn't
active, the current line is shifted.  The shifted region includes
the lines in which START and END lie.  An error is signaled if
any lines in the region are indented less than COUNT columns."
  (interactive
   (if mark-active
       (list (region-beginning) (region-end) current-prefix-arg)
     (list (line-beginning-position) (line-end-position) current-prefix-arg)))
  (if count
      (setq count (prefix-numeric-value count))
    (setq count kivy-indent-offset))
  (when (> count 0)
    (let ((deactivate-mark nil))
      (save-excursion
        (goto-char start)
        (while (< (point) end)
          (if (and (< (current-indentation) count)
                   (not (looking-at "[ \t]*$")))
              (error "Can't shift all lines enough"))
          (forward-line))
        (indent-rigidly start end (- count))))))

(defun kivy-indent-shift-right (start end &optional count)
  "Shift lines contained in region START END by COUNT columns to the left.
COUNT defaults to `kivy-indent-offset'.  If region isn't
active, the current line is shifted.  The shifted region includes
the lines in which START and END lie."
  (interactive
   (if mark-active
       (list (region-beginning) (region-end) current-prefix-arg)
     (list (line-beginning-position) (line-end-position) current-prefix-arg)))
  (let ((deactivate-mark nil))
    (if count
        (setq count (prefix-numeric-value count))
      (setq count kivy-indent-offset))
    (indent-rigidly start end count)))

(provide 'kivy-mode)

;;; kivy-mode.el ends here
