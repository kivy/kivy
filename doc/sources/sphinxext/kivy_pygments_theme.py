# kivy pygments style based on flask/tango style
from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, \
     Number, Operator, Generic, Whitespace, Punctuation, Other, Literal


class KivyStyle(Style):
    # The background color is set in kivystyle.sty
    background_color = ""
    default_style = ""

    styles = {
        # No corresponding class for the following:
        #Text:                     "", # class:  ''
        Whitespace:                "underline #ffffff",      # class: 'w'
        Error:                     "#FF0000 border:#FF0000", # class: 'err'
        Other:                     "#FF0000",                # class 'x'

        Comment:                   "italic #666385", # class: 'c'
        Comment.Preproc:           "noitalic",       # class: 'cp'

        Keyword:                   "bold #000000",   # class: 'k'
        Keyword.Constant:          "bold #000000",   # class: 'kc'
        Keyword.Declaration:       "bold #000000",   # class: 'kd'
        Keyword.Namespace:         "bold #000000",   # class: 'kn'
        Keyword.Pseudo:            "bold #000000",   # class: 'kp'
        Keyword.Reserved:          "bold #000000",   # class: 'kr'
        Keyword.Type:              "bold #000000",   # class: 'kt'

        Operator:                  "#582800",   # class: 'o'
        Operator.Word:             "bold #000000",   # class: 'ow' - like keywords

        Punctuation:               "bold #000000",   # class: 'p'

        # because special names such as Name.Class, Name.Function, etc.
        # are not recognized as such later in the parsing, we choose them
        # to look the same as ordinary variables.
        Name:                      "#000000",        # class: 'n'
        Name.Attribute:            "#c4a000",        # class: 'na' - to be revised
        Name.Builtin:              "#000000",        # class: 'nb'
        Name.Builtin.Pseudo:       "#aa1105",        # class: 'bp'
        Name.Class:                "#db6500",        # class: 'nc' - to be revised
        Name.Constant:             "#000000",        # class: 'no' - to be revised
        Name.Decorator:            "#888",           # class: 'nd' - to be revised
        Name.Entity:               "#ce5c00",        # class: 'ni'
        Name.Exception:            "bold #cc0000",   # class: 'ne'
        Name.Function:             "#db6500",        # class: 'nf'
        Name.Property:             "#000000",        # class: 'py'
        Name.Label:                "#f57900",        # class: 'nl'
        Name.Namespace:            "#000000",        # class: 'nn' - to be revised
        Name.Other:                "#000000",        # class: 'nx'
        Name.Tag:                  "bold #004461",   # class: 'nt' - like a keyword
        Name.Variable:             "#000000",        # class: 'nv' - to be revised
        Name.Variable.Class:       "#000000",        # class: 'vc' - to be revised
        Name.Variable.Global:      "#000000",        # class: 'vg' - to be revised
        Name.Variable.Instance:    "#000000",        # class: 'vi' - to be revised

        Number:                    "#990000",        # class: 'm'

        Literal:                   "#000000",        # class: 'l'
        Literal.Date:              "#000000",        # class: 'ld'

        String:                    "#74171b",        # class: 's'
        String.Backtick:           "#4e9a06",        # class: 'sb'
        String.Char:               "#4e9a06",        # class: 'sc'
        String.Doc:                "italic #640000", # class: 'sd' - like a comment
        String.Double:             "#74171b",        # class: 's2'
        String.Escape:             "#74171b",        # class: 'se'
        String.Heredoc:            "#74171b",        # class: 'sh'
        String.Interpol:           "#74171b",        # class: 'si'
        String.Other:              "#74171b",        # class: 'sx'
        String.Regex:              "#74171b",        # class: 'sr'
        String.Single:             "#74171b",        # class: 's1'
        String.Symbol:             "#74171b",        # class: 'ss'

        Generic:                   "#000000",        # class: 'g'
        Generic.Deleted:           "#a40000",        # class: 'gd'
        Generic.Emph:              "italic #000000", # class: 'ge'
        Generic.Error:             "#ef2929",        # class: 'gr'
        Generic.Heading:           "bold #000080",   # class: 'gh'
        Generic.Inserted:          "#00A000",        # class: 'gi'
        Generic.Output:            "#888",           # class: 'go'
        Generic.Prompt:            "#745334",        # class: 'gp'
        Generic.Strong:            "bold #000000",   # class: 'gs'
        Generic.Subheading:        "bold #800080",   # class: 'gu'
        Generic.Traceback:         "bold #a40000",   # class: 'gt'
    }
