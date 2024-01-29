# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.text import Label as CoreLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.spinner import SpinnerOption
from kivy.uix.popup import Popup
import os


Builder.load_string('''
#: import utils kivy
#: import os os
#: import Factory kivy.factory.Factory
<FntSpinnerOption>
    font_name: self.text if self.text else self.font_name

<Unicode_TextInput>
    orientation: 'vertical'
    txt_input: unicode_txt
    spnr_fnt: fnt_spnr
    BoxLayout:
        size_hint: 1, .05
        Spinner:
            id: fnt_spnr
            text: 'RobotoMono-Regular'
            font_name: self.text if self.text else self.font_name
            values: app.get_font_list
            option_cls: Factory.FntSpinnerOption
        Spinner:
            id: fntsz_spnr
            text: '15'
            values: map(str, map(sp, range(5,39)))
    ScrollView:
        size_hint: 1, .9
        TextInput:
            id: unicode_txt
            background_color: .8811, .8811, .8811, 1
            foreground_color: 0, 0, 0, 1
            font_name: fnt_spnr.font_name
            font_size: sp(fntsz_spnr.text or 0)
            text: root.unicode_string
            size_hint: 1, None
            height: self.minimum_height
    BoxLayout:
        size_hint: 1, .05
        Label:
            text: 'current font: ' + unicode_txt.font_name
        Button:
            size_hint: .15, 1
            text: 'change Font ...'
            valign: 'middle'
            halign: 'center'
            text_size: self.size
            on_release: root.show_load()

<LoadDialog>:
    platform: utils.platform
    BoxLayout:
        size: root.size
        pos: root.pos
        BoxLayout:
            orientation: "vertical"
            size_hint: .2, 1
            Button:
                size_hint: 1, .2
                text: 'User font directory\\n'
                valign: 'middle'
                halign: 'center'
                text_size: self.size
                on_release:
                    _platform = root.platform
                    filechooser.path = (os.path.expanduser('~/.fonts')
                    if _platform == 'linux' else '/system/fonts'
                    if _platform == 'android'
                    else os.path.expanduser('~/Library/Fonts')
                    if _platform == 'macosx'
                    else os.environ['WINDIR'] +'\\Fonts\')
            Button:
                size_hint: 1, .2
                text: 'System Font directory'
                valign: 'middle'
                halign: 'center'
                text_size: self.size
                on_release:
                    _platform = root.platform
                    filechooser.path = ('/usr/share/fonts'
                    if _platform == 'linux' else '/system/fonts'
                    if _platform == 'android' else os.path.expanduser
                    ('/System/Library/Fonts') if _platform == 'macosx'
                    else os.environ['WINDIR'] + "\\Fonts\")
            Label:
                text: 'BookMarks'
        BoxLayout:
            orientation: "vertical"
            FileChooserListView:
                id: filechooser
                filters: ['*.ttf']
            BoxLayout:
                size_hint_y: None
                height: 30
                Button:
                    text: "cancel"
                    on_release: root.cancel()
                Button:
                    text: "load"
                    on_release: filechooser.selection != [] and root.load\
(filechooser.path, filechooser.selection)
''')


class FntSpinnerOption(SpinnerOption):
    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Unicode_TextInput(BoxLayout):

    txt_input = ObjectProperty(None)
    unicode_string = StringProperty("""Latin-1 supplement: éé çç ßß

List of major languages taken from Google Translate
____________________________________________________
Try changing the font to see if the font can render the glyphs you need in your
application. Scroll to see all languages in the list.

Basic Latin:    The quick brown fox jumps over the lazy old dog.
Albanian:       Kafe të shpejtë dhelpra hedhje mbi qen lazy vjetër.
الثعلب البني السريع يقفز فوق الكلب القديمة البطيئة.         :Arabic
Africans:       Die vinnige bruin jakkals spring oor die lui hond.
Armenian:       Արագ Brown Fox jumps ավելի ծույլ հին շունը.
Azerbaijani:    Tez qonur tülkü də tənbəl yaşlı it üzərində atlamalar.
Basque:         Azkar marroia fox alferrak txakur zaharra baino gehiago jauzi.
Belarusian:     Хуткі карычневы ліс пераскоквае праз гультаяваты стары сабака.
Bengali:        দ্রুত বাদামী শিয়াল অলস পুরানো কুকুর বেশি
Bulgarian:      Бързата кафява лисица скача над мързелив куче.
Chinese Simpl:  敏捷的棕色狐狸跳过懒惰的老狗。
Catalan:        La cigonya tocava el saxofon en el vell gos mandrós.
Croation:       Brzo smeđa lisica skoči preko lijen stari pas.
Czech:          Rychlá hnědá liška skáče přes líného starého psa.
Danish:         Den hurtige brune ræv hopper over den dovne gamle hund.
Dutch:          De snelle bruine vos springt over de luie oude hond.
Estonian:       Kiire pruun rebane hüppab üle laisa vana koer.
Filipino:       Ang mabilis na brown soro jumps sa ang tamad lumang aso.
Finnish:        Nopea ruskea kettu hyppää yli laiska vanha koira.
French:         Le renard brun rapide saute par dessus le chien
                paresseux vieux.
Galician:       A lixeira raposo marrón ataca o can preguiceiro de idade.
Gregorian:      სწრაფი ყავისფერი მელა jumps გამო ზარმაცი წლის ძაღლი.
German:         Der schnelle braune Fuchs springt über den faulen alten Hund.
Greek:          Η γρήγορη καφέ αλεπού πηδάει πάνω από το τεμπέλικο
                γέρικο σκυλί.
Gujrati:        આ ઝડપી ભુરો શિયાળ તે બેકાર જૂના કૂતરા પર કૂદકા.
Gurmukhi:       ਤੇਜ ਭੂਰੇ ਰੰਗ ਦੀ ਲੋਮੜੀ ਆਲਸੀ ਬੁੱਢੇ ਕੁੱਤੇ ਦੇ ਉਤੋਂ ਦੀ ਟੱਪਦੀ ਹੈ ।
Hiation Creole: Rapid mawon Rena a so sou chen an parese fin vye granmoun.
Hebrew:         השועל החום הזריז קופץ על הכלב הישן עצלן.
Hindi:          तेज भूरे रंग की लोमड़ी आलसी बूढ़े कुत्ते के उपर से कूदती है ॥
Hungarian:      A gyors barna róka átugorja a lusta vén kutya.
Icelandic:      The fljótur Brown refur stökk yfir latur gamall hundur.
Indonesian:     Cepat rubah cokelat melompat atas anjing tua malas.
Irish:          An sionnach donn tapaidh jumps thar an madra leisciúil d\'aois.
Italian:        The quick brown fox salta sul cane pigro vecchio.
Japanese:       速い茶色のキツネは、のろまな古いイヌに飛びかかった。
Kannada:        ತ್ವರಿತ ಕಂದು ನರಿ ಆಲೂಗಡ್ಡೆ ಹಳೆಯ ಶ್ವಾನ ಮೇಲೆ ಜಿಗಿತಗಳು.
Korean:         무궁화 게으른 옛 피었습니다.
Latin:          Vivamus adipiscing orci et rutrum tincidunt super vetus canis.
Latvian:        Ātra brūna lapsa lec pāri slinkam vecs suns.
Lithuanian:     Greita ruda lapė šokinėja per tingus senas šuo.
Macedonian:     Брзата кафена лисица скокови над мрзливи стариот пес.
Malay:          Fox coklat cepat melompat atas anjing lama malas.
Maltese:        Il-volpi kannella malajr jumps fuq il-kelb qodma għażżien.
Norweigian:     Den raske brune reven hopper over den late gamle hunden.
Persian:        روباه قهوه ای سریع روی سگ تنبل قدیمی میپرد.
Polish:         Szybki brązowy lis przeskoczył nad leniwym psem życia.
Portugese:      A ligeira raposa marrom ataca o cão preguiçoso de idade.
Romanian:       Rapidă maro vulpea sare peste cainele lenes vechi.
Russian:        Быстрая коричневая лисица перепрыгивает ленивого старого пса.
Serniam:        Брза смеђа лисица прескаче лењог пса старог.
Slovak:         Rýchla hnedá líška skáče cez lenivého starého psa.
Slovenian:      Kožuščku hudobnega nad leni starega psa.
Spanish:        La cigüeña tocaba el saxofón en el viejo perro perezoso.
Swahili:        Haraka brown fox anaruka juu ya mbwa wavivu zamani.
Swedish:        Den snabba bruna räven hoppar över den lata gammal hund.
Tamil:          விரைவான பிரவுன் ஃபாக்ஸ் சோம்பேறி பழைய நாய் மீது
                தொடரப்படுகிறது
Telugu:         శీఘ్ర బ్రౌన్ ఫాక్స్ సోమరితనం పాత కుక్క కంటే హెచ్చుతగ్గుల.
Thai:           สีน้ำตาลอย่างรวดเร็วจิ้งจอกกระโดดมากกว่าสุนัขเก่าที่ขี้เกียจ
Turkish:        Hızlı kahverengi tilki tembel köpeğin üstünden atlar.
Ukrainian:       Швидкий коричневий лис перестрибує через лінивий старий пес.
Urdu:           فوری بھوری لومڑی سست بوڑھے کتے پر کودتا.
Vietnamese:     Các con cáo nâu nhanh chóng nhảy qua con chó lười biếng cũ.
Welsh:          Mae'r cyflym frown llwynog neidio dros y ci hen ddiog.
Yiddish:        דער גיך ברוין פוקס דזשאַמפּס איבער די פויל אַלט הונט.""")

    def dismiss_popup(self):
        self._popup.dismiss()

    def load(self, _path, _fname):
        self.txt_input.font_name = _fname[0]
        _f_name = _fname[0][_fname[0].rfind(os.sep) + 1:]
        self.spnr_fnt.text = _f_name[:_f_name.rfind('.')]
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="load file", content=content,
            size_hint=(0.9, 0.9))
        self._popup.open()


from kivy.utils import reify


class unicode_app(App):

    def build(self):
        return Unicode_TextInput()

    @reify
    def get_font_list(self):
        '''Get a list of all the fonts available on this system.
        '''

        fonts_path = CoreLabel.get_system_fonts_dir()
        flist = []

        for fdir in fonts_path:
            for fpath in sorted(os.listdir(fdir)):
                if fpath.endswith('.ttf'):
                    flist.append(fpath[:-4])

        return sorted(flist)


if __name__ == '__main__':

    unicode_app().run()
