# -*- coding: utf-8 -*-

# This work is licensed under the GNU Public License (GPL).
# To view a copy of this license, visit http://www.gnu.org/copyleft/gpl.html

# Written by Abd Allah Diab (mpcabd)
# Email: mpcabd ^at^ gmail ^dot^ com
# Website: http://mpcabd.igeex.biz

# Ported and tweaked from Java to Python, from Better Arabic Reshaper [https://github.com/agawish/Better-Arabic-Reshaper/]

# Usage:
### Install python-bidi [https://github.com/MeirKriheli/python-bidi], can be installed from pip `pip install python-bidi`.

# import arabic_reshaper
# from bidi.algorithm import get_display
# reshaped_text = arabic_reshaper.reshape(u'اللغة العربية رائعة')
# bidi_text = get_display(reshaped_text)
### Now you can pass `bidi_text` to any function that handles displaying/printing of the text, like writing it to PIL Image or passing it to a PDF generating method.

import re

DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_MDD 		= u'\u0622'
DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_HAMAZA		= u'\u0623'
DEFINED_CHARACTERS_ORGINAL_ALF_LOWER_HAMAZA 	= u'\u0625'
DEFINED_CHARACTERS_ORGINAL_ALF 					= u'\u0627'
DEFINED_CHARACTERS_ORGINAL_LAM					= u'\u0644'

LAM_ALEF_GLYPHS = [
	[u'\u3BA6', u'\uFEF6', u'\uFEF5'],
	[u'\u3BA7', u'\uFEF8', u'\uFEF7'],
	[u'\u0627', u'\uFEFC', u'\uFEFB'],
	[u'\u0625', u'\uFEFA', u'\uFEF9']
]

HARAKAT = [
	u'\u0600', u'\u0601', u'\u0602', u'\u0603', u'\u0606', u'\u0607', u'\u0608', u'\u0609',
	u'\u060A', u'\u060B', u'\u060D', u'\u060E', u'\u0610', u'\u0611', u'\u0612', u'\u0613',
	u'\u0614', u'\u0615', u'\u0616', u'\u0617', u'\u0618', u'\u0619', u'\u061A', u'\u061B',
	u'\u061E', u'\u061F', u'\u0621', u'\u063B', u'\u063C', u'\u063D', u'\u063E', u'\u063F',
	u'\u0640', u'\u064B', u'\u064C', u'\u064D', u'\u064E', u'\u064F', u'\u0650', u'\u0651',
	u'\u0652', u'\u0653', u'\u0654', u'\u0655', u'\u0656', u'\u0657', u'\u0658', u'\u0659',
	u'\u065A', u'\u065B', u'\u065C', u'\u065D', u'\u065E', u'\u0660', u'\u066A', u'\u066B',
	u'\u066C', u'\u066F', u'\u0670', u'\u0672', u'\u06D4', u'\u06D5', u'\u06D6', u'\u06D7',
	u'\u06D8', u'\u06D9', u'\u06DA', u'\u06DB', u'\u06DC', u'\u06DF', u'\u06E0', u'\u06E1',
	u'\u06E2', u'\u06E3', u'\u06E4', u'\u06E5', u'\u06E6', u'\u06E7', u'\u06E8', u'\u06E9',
	u'\u06EA', u'\u06EB', u'\u06EC', u'\u06ED', u'\u06EE', u'\u06EF', u'\u06D6', u'\u06D7',
	u'\u06D8', u'\u06D9', u'\u06DA', u'\u06DB', u'\u06DC', u'\u06DD', u'\u06DE', u'\u06DF',
	u'\u06F0', u'\u06FD', u'\uFE70', u'\uFE71', u'\uFE72', u'\uFE73', u'\uFE74', u'\uFE75',
	u'\uFE76', u'\uFE77', u'\uFE78', u'\uFE79', u'\uFE7A', u'\uFE7B', u'\uFE7C', u'\uFE7D',
	u'\uFE7E', u'\uFE7F', u'\uFC5E', u'\uFC5F', u'\uFC60', u'\uFC61', u'\uFC62', u'\uFC63'
]

ARABIC_GLYPHS = {
	u'\u0622' : [u'\u0622', u'\uFE81', u'\uFE81', u'\uFE82', u'\uFE82', 2],
	u'\u0623' : [u'\u0623', u'\uFE83', u'\uFE83', u'\uFE84', u'\uFE84', 2],
	u'\u0624' : [u'\u0624', u'\uFE85', u'\uFE85', u'\uFE86', u'\uFE86', 2],
	u'\u0625' : [u'\u0625', u'\uFE87', u'\uFE87', u'\uFE88', u'\uFE88', 2],
	u'\u0626' : [u'\u0626', u'\uFE89', u'\uFE8B', u'\uFE8C', u'\uFE8A', 4],
	u'\u0627' : [u'\u0627', u'\u0627', u'\u0627', u'\uFE8E', u'\uFE8E', 2],
	u'\u0628' : [u'\u0628', u'\uFE8F', u'\uFE91', u'\uFE92', u'\uFE90', 4],
	u'\u0629' : [u'\u0629', u'\uFE93', u'\uFE93', u'\uFE94', u'\uFE94', 2],
	u'\u062A' : [u'\u062A', u'\uFE95', u'\uFE97', u'\uFE98', u'\uFE96', 4],
	u'\u062B' : [u'\u062B', u'\uFE99', u'\uFE9B', u'\uFE9C', u'\uFE9A', 4],
	u'\u062C' : [u'\u062C', u'\uFE9D', u'\uFE9F', u'\uFEA0', u'\uFE9E', 4],
	u'\u062D' : [u'\u062D', u'\uFEA1', u'\uFEA3', u'\uFEA4', u'\uFEA2', 4],
	u'\u062E' : [u'\u062E', u'\uFEA5', u'\uFEA7', u'\uFEA8', u'\uFEA6', 4],
	u'\u062F' : [u'\u062F', u'\uFEA9', u'\uFEA9', u'\uFEAA', u'\uFEAA', 2],
	u'\u0630' : [u'\u0630', u'\uFEAB', u'\uFEAB', u'\uFEAC', u'\uFEAC', 2],
	u'\u0631' : [u'\u0631', u'\uFEAD', u'\uFEAD', u'\uFEAE', u'\uFEAE', 2],
	u'\u0632' : [u'\u0632', u'\uFEAF', u'\uFEAF', u'\uFEB0', u'\uFEB0', 2],
	u'\u0633' : [u'\u0633', u'\uFEB1', u'\uFEB3', u'\uFEB4', u'\uFEB2', 4],
	u'\u0634' : [u'\u0634', u'\uFEB5', u'\uFEB7', u'\uFEB8', u'\uFEB6', 4],
	u'\u0635' : [u'\u0635', u'\uFEB9', u'\uFEBB', u'\uFEBC', u'\uFEBA', 4],
	u'\u0636' : [u'\u0636', u'\uFEBD', u'\uFEBF', u'\uFEC0', u'\uFEBE', 4],
	u'\u0637' : [u'\u0637', u'\uFEC1', u'\uFEC3', u'\uFEC4', u'\uFEC2', 4],
	u'\u0638' : [u'\u0638', u'\uFEC5', u'\uFEC7', u'\uFEC8', u'\uFEC6', 4],
	u'\u0639' : [u'\u0639', u'\uFEC9', u'\uFECB', u'\uFECC', u'\uFECA', 4],
	u'\u063A' : [u'\u063A', u'\uFECD', u'\uFECF', u'\uFED0', u'\uFECE', 4],
	u'\u0641' : [u'\u0641', u'\uFED1', u'\uFED3', u'\uFED4', u'\uFED2', 4],
	u'\u0642' : [u'\u0642', u'\uFED5', u'\uFED7', u'\uFED8', u'\uFED6', 4],
	u'\u0643' : [u'\u0643', u'\uFED9', u'\uFEDB', u'\uFEDC', u'\uFEDA', 4],
	u'\u0644' : [u'\u0644', u'\uFEDD', u'\uFEDF', u'\uFEE0', u'\uFEDE', 4],
	u'\u0645' : [u'\u0645', u'\uFEE1', u'\uFEE3', u'\uFEE4', u'\uFEE2', 4],
	u'\u0646' : [u'\u0646', u'\uFEE5', u'\uFEE7', u'\uFEE8', u'\uFEE6', 4],
	u'\u0647' : [u'\u0647', u'\uFEE9', u'\uFEEB', u'\uFEEC', u'\uFEEA', 4],
	u'\u0648' : [u'\u0648', u'\uFEED', u'\uFEED', u'\uFEEE', u'\uFEEE', 2],
	u'\u0649' : [u'\u0649', u'\uFEEF', u'\uFEEF', u'\uFEF0', u'\uFEF0', 2],
	u'\u0671' : [u'\u0671', u'\u0671', u'\u0671', u'\uFB51', u'\uFB51', 2],
	u'\u064A' : [u'\u064A', u'\uFEF1', u'\uFEF3', u'\uFEF4', u'\uFEF2', 4],
	u'\u066E' : [u'\u066E', u'\uFBE4', u'\uFBE8', u'\uFBE9', u'\uFBE5', 4],
	u'\u06AA' : [u'\u06AA', u'\uFB8E', u'\uFB90', u'\uFB91', u'\uFB8F', 4],
	u'\u06C1' : [u'\u06C1', u'\uFBA6', u'\uFBA8', u'\uFBA9', u'\uFBA7', 4],
	u'\u06E4' : [u'\u06E4', u'\u06E4', u'\u06E4', u'\u06E4', u'\uFEEE', 2],
	u'\u067E' : [u'\u067E', u'\uFB56', u'\uFB58', u'\uFB59', u'\uFB57', 4],
	u'\u0698' : [u'\u0698', u'\uFB8A', u'\uFB8A', u'\uFB8A', u'\uFB8B', 2],
	u'\u06AF' : [u'\u06AF', u'\uFB92', u'\uFB94', u'\uFB95', u'\uFB93', 4],
	u'\u0686' : [u'\u0686', u'\uFB7A', u'\uFB7C', u'\uFB7D', u'\uFB7B', 4],
	u'\u06A9' : [u'\u06A9', u'\uFB8E', u'\uFB90', u'\uFB91', u'\uFB8F', 4],
	u'\u06CC' : [u'\u06CC', u'\uFEEF', u'\uFEF3', u'\uFEF4', u'\uFEF0', 4]
}

ARABIC_GLYPHS_LIST = [
	[u'\u0622', u'\uFE81', u'\uFE81', u'\uFE82', u'\uFE82', 2],
	[u'\u0623', u'\uFE83', u'\uFE83', u'\uFE84', u'\uFE84', 2],
	[u'\u0624', u'\uFE85', u'\uFE85', u'\uFE86', u'\uFE86', 2],
	[u'\u0625', u'\uFE87', u'\uFE87', u'\uFE88', u'\uFE88', 2],
	[u'\u0626', u'\uFE89', u'\uFE8B', u'\uFE8C', u'\uFE8A', 4],
	[u'\u0627', u'\u0627', u'\u0627', u'\uFE8E', u'\uFE8E', 2],
	[u'\u0628', u'\uFE8F', u'\uFE91', u'\uFE92', u'\uFE90', 4],
	[u'\u0629', u'\uFE93', u'\uFE93', u'\uFE94', u'\uFE94', 2],
	[u'\u062A', u'\uFE95', u'\uFE97', u'\uFE98', u'\uFE96', 4],
	[u'\u062B', u'\uFE99', u'\uFE9B', u'\uFE9C', u'\uFE9A', 4],
	[u'\u062C', u'\uFE9D', u'\uFE9F', u'\uFEA0', u'\uFE9E', 4],
	[u'\u062D', u'\uFEA1', u'\uFEA3', u'\uFEA4', u'\uFEA2', 4],
	[u'\u062E', u'\uFEA5', u'\uFEA7', u'\uFEA8', u'\uFEA6', 4],
	[u'\u062F', u'\uFEA9', u'\uFEA9', u'\uFEAA', u'\uFEAA', 2],
	[u'\u0630', u'\uFEAB', u'\uFEAB', u'\uFEAC', u'\uFEAC', 2],
	[u'\u0631', u'\uFEAD', u'\uFEAD', u'\uFEAE', u'\uFEAE', 2],
	[u'\u0632', u'\uFEAF', u'\uFEAF', u'\uFEB0', u'\uFEB0', 2],
	[u'\u0633', u'\uFEB1', u'\uFEB3', u'\uFEB4', u'\uFEB2', 4],
	[u'\u0634', u'\uFEB5', u'\uFEB7', u'\uFEB8', u'\uFEB6', 4],
	[u'\u0635', u'\uFEB9', u'\uFEBB', u'\uFEBC', u'\uFEBA', 4],
	[u'\u0636', u'\uFEBD', u'\uFEBF', u'\uFEC0', u'\uFEBE', 4],
	[u'\u0637', u'\uFEC1', u'\uFEC3', u'\uFEC4', u'\uFEC2', 4],
	[u'\u0638', u'\uFEC5', u'\uFEC7', u'\uFEC8', u'\uFEC6', 4],
	[u'\u0639', u'\uFEC9', u'\uFECB', u'\uFECC', u'\uFECA', 4],
	[u'\u063A', u'\uFECD', u'\uFECF', u'\uFED0', u'\uFECE', 4],
	[u'\u0641', u'\uFED1', u'\uFED3', u'\uFED4', u'\uFED2', 4],
	[u'\u0642', u'\uFED5', u'\uFED7', u'\uFED8', u'\uFED6', 4],
	[u'\u0643', u'\uFED9', u'\uFEDB', u'\uFEDC', u'\uFEDA', 4],
	[u'\u0644', u'\uFEDD', u'\uFEDF', u'\uFEE0', u'\uFEDE', 4],
	[u'\u0645', u'\uFEE1', u'\uFEE3', u'\uFEE4', u'\uFEE2', 4],
	[u'\u0646', u'\uFEE5', u'\uFEE7', u'\uFEE8', u'\uFEE6', 4],
	[u'\u0647', u'\uFEE9', u'\uFEEB', u'\uFEEC', u'\uFEEA', 4],
	[u'\u0648', u'\uFEED', u'\uFEED', u'\uFEEE', u'\uFEEE', 2],
	[u'\u0649', u'\uFEEF', u'\uFEEF', u'\uFEF0', u'\uFEF0', 2],
	[u'\u0671', u'\u0671', u'\u0671', u'\uFB51', u'\uFB51', 2],
	[u'\u064A', u'\uFEF1', u'\uFEF3', u'\uFEF4', u'\uFEF2', 4],
	[u'\u066E', u'\uFBE4', u'\uFBE8', u'\uFBE9', u'\uFBE5', 4],
	[u'\u06AA', u'\uFB8E', u'\uFB90', u'\uFB91', u'\uFB8F', 4],
	[u'\u06C1', u'\uFBA6', u'\uFBA8', u'\uFBA9', u'\uFBA7', 4],
	[u'\u067E', u'\uFB56', u'\uFB58', u'\uFB59', u'\uFB57', 4],
	[u'\u0698', u'\uFB8A', u'\uFB8A', u'\uFB8A', u'\uFB8B', 2],
	[u'\u06AF', u'\uFB92', u'\uFB94', u'\uFB95', u'\uFB93', 4],
	[u'\u0686', u'\uFB7A', u'\uFB7C', u'\uFB7D', u'\uFB7B', 4],
	[u'\u06A9', u'\uFB8E', u'\uFB90', u'\uFB91', u'\uFB8F', 4],
	[u'\u06CC', u'\uFEEF', u'\uFEF3', u'\uFEF4', u'\uFEF0', 4]
]

def get_reshaped_glyph(target, location):
	if target in ARABIC_GLYPHS:
		return ARABIC_GLYPHS[target][location]
	else:
		return target
		
def get_glyph_type(target):
	if target in ARABIC_GLYPHS:
		return ARABIC_GLYPHS[target][5]
	else:
		return 2
		
def is_haraka(target):
	return target in HARAKAT

def replace_jalalah(unshaped_word):
	return re.sub(u'^\u0627\u0644\u0644\u0647$', u'\uFDF2', unshaped_word)

def replace_lam_alef(unshaped_word):
	list_word = list(unshaped_word)
	letter_before = u''
	for i in range(len(unshaped_word)):
		if not is_haraka(unshaped_word[i]) and unshaped_word[i] != DEFINED_CHARACTERS_ORGINAL_LAM:
			letter_before = unshaped_word[i]

		if unshaped_word[i] == DEFINED_CHARACTERS_ORGINAL_LAM:
			candidate_lam = unshaped_word[i]
			lam_position = i
			haraka_position = i + 1
			
			while haraka_position < len(unshaped_word) and is_haraka(unshaped_word[haraka_position]):
				haraka_position += 1
				
			if haraka_position < len(unshaped_word):
				if lam_position > 0 and get_glyph_type(letter_before) > 2:
					lam_alef = get_lam_alef(list_word[haraka_position], candidate_lam, False)
				else:
					lam_alef = get_lam_alef(list_word[haraka_position], candidate_lam, True)
				if lam_alef != '':
					list_word[lam_position] = lam_alef
					list_word[haraka_position] = u' '
			
	return u''.join(list_word).replace(u' ', u'')
		
def get_lam_alef(candidate_alef, candidate_lam, is_end_of_word):
	shift_rate = 1
	reshaped_lam_alef = u''
	if is_end_of_word:
		shift_rate += 1
	
	if DEFINED_CHARACTERS_ORGINAL_LAM == candidate_lam:
		if DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_MDD == candidate_alef:
			reshaped_lam_alef = LAM_ALEF_GLYPHS[0][shift_rate]
		
		if DEFINED_CHARACTERS_ORGINAL_ALF_UPPER_HAMAZA == candidate_alef:
			reshaped_lam_alef = LAM_ALEF_GLYPHS[1][shift_rate]
		
		if DEFINED_CHARACTERS_ORGINAL_ALF == candidate_alef:
			reshaped_lam_alef = LAM_ALEF_GLYPHS[2][shift_rate]
		
		if DEFINED_CHARACTERS_ORGINAL_ALF_LOWER_HAMAZA == candidate_alef:
			reshaped_lam_alef = LAM_ALEF_GLYPHS[3][shift_rate]
	
	return reshaped_lam_alef

class DecomposedWord(object):
	def __init__(self, word):
		self.stripped_harakat = []
		self.harakat_positions = []
		self.stripped_regular_letters = []
		self.letters_position = []

		for i in range(len(word)):
			c = word[i]
			if is_haraka(c):
				self.harakat_positions.append(i)
				self.stripped_harakat.append(c)
			else:
				self.letters_position.append(i)
				self.stripped_regular_letters.append(c)

	def reconstruct_word(self, reshaped_word):
		l = list(u'\0' * (len(self.stripped_harakat) + len(reshaped_word)))
		for i in range(len(self.letters_position)):
			l[self.letters_position[i]] = reshaped_word[i]
		for i in range(len(self.harakat_positions)):
			l[self.harakat_positions[i]] = self.stripped_harakat[i]
		return u''.join(l)

def get_reshaped_word(unshaped_word):
	unshaped_word = replace_jalalah(unshaped_word)
	unshaped_word = replace_lam_alef(unshaped_word)
	decomposed_word = DecomposedWord(unshaped_word)
	result = u''
	if decomposed_word.stripped_regular_letters:
		result = reshape_it(u''.join(decomposed_word.stripped_regular_letters))
	return decomposed_word.reconstruct_word(result)

def reshape_it(unshaped_word):
	if not unshaped_word:
		return u''
	if len(unshaped_word) == 1:
		return get_reshaped_glyph(unshaped_word[0], 1)
	reshaped_word = []
	for i in range(len(unshaped_word)):
		before = False
		after = False
		if i == 0:
			after = get_glyph_type(unshaped_word[i]) == 4
		elif i == len(unshaped_word) - 1:
			before = get_glyph_type(unshaped_word[i - 1]) == 4
		else:
			after = get_glyph_type(unshaped_word[i]) == 4
			before = get_glyph_type(unshaped_word[i - 1]) == 4
		if after and before:
			reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 3))
		elif after and not before:
			reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 2))
		elif not after and before:
			reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 4))
		elif not after and not before:
			reshaped_word.append(get_reshaped_glyph(unshaped_word[i], 1))

	return u''.join(reshaped_word)


def is_arabic_character(target):
	return target in ARABIC_GLYPHS or target in HARAKAT
	
def get_words(sentence):
	if sentence:
		return re.split('\\s', sentence)
	return []
	
def has_arabic_letters(word):
	for c in word:
		if is_arabic_character(c):
			return True
	return False

def is_arabic_word(word):
	for c in word:
		if not is_arabic_character(c):
			return False
	return True
	
def get_words_from_mixed_word(word):
	temp_word = u''
	words = []
	for c in word:
		if is_arabic_character(c):
			if temp_word and not is_arabic_word(temp_word):
				words.append(temp_word)
				temp_word = c
			else:
				temp_word += c
		else:
			if temp_word and is_arabic_word(temp_word):
				words.append(temp_word)
				temp_word = c
			else:
				temp_word += c
	if temp_word:
		words.append(temp_word)
	return words
	
def reshape(text):
	if text:
		lines = re.split('\\r?\\n', text)
		for i in range(len(lines)):
			lines[i] = reshape_sentence(lines[i])
		return u'\n'.join(lines)
	return u''
	
def reshape_sentence(sentence):
	words = get_words(sentence)
	for i in range(len(words)):
		word = words[i]
		if has_arabic_letters(word):
			if is_arabic_word(word):
				words[i] = get_reshaped_word(word)
			else:
				mixed_words = get_words_from_mixed_word(word)
				for j in range(len(mixed_words)):
					mixed_words[j] = get_reshaped_word(mixed_words[j])
				words[i] = u''.join(mixed_words)
	return u' '.join(words)
