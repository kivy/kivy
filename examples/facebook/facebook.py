# -*- coding: utf-8 -
import json
from kivy.app import App
import os
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from functools import partial
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
import webbrowser

#edit Facebook developer crenedtials here
FB_ID = ""
FB_SECRET = ""

root = GridLayout(cols=1, spacing=0)


class TestApp(App):
    def update_progress(self, *args):
        pass

    def on_progress(self, req, cur_sz, tot_sz):
        Clock.schedule_once(partial(self.update_progress,
        req, cur_sz, tot_sz), 1)

    def store_fb_feed(self, req, result):
        if len(result) > 0 and req.resp_status == 200:
            f = open('fbfeed.txt', 'w')
            f.write(str(result))
            f.close()
            self.CreateFaceBook()

    def success_fb_token(self, req, result):
        if len(result) > 0 and req.resp_status == 200:
            token = result
            url = "https://graph.facebook.com/127423910605493/feed?%s" % (token)
            self.fb_get = UrlRequest(url,
                timeout=15,
                on_success=self.store_fb_feed,
                on_progress=self.on_progress)

    def getfbfile(self, *args):

        url = "https://graph.facebook.com/oauth/access_token?"\
            "grant_type=client_credentials&client_id=%"\
            "s&client_secret=%s" % (FB_ID, FB_SECRET)
        self.fb = UrlRequest(url,
                timeout=15,
                on_success=self.success_fb_token,
                on_progress=self.on_progress)

    def openweb(self, url):
        webbrowser.open(url)

    def CreateFaceBook(self):
        def parsefbfile():
            out = []
            fa = open("fbfeed.txt", mode="r")
            a = fa.read()
            try:
                all = json.loads(a)
                all = all['data']
                for i in all:
                    entry = []
                    title = ''
                    link = 'http://www.facebook.com/127423910605493/'
                    post_type = ''
                    likes = '0'
                    comments = '0'
                    picture = ''
                    message = ''
                    timestamp = ''
                    if i.get('type'):
                        post_type = i['type']
                    if post_type == 'status' or post_type == 'photo':
                        if i.get('message'):
                            message = i['message']
                        else:
                            if i.get('story'):
                                message = i['story']

                    if i.get('created_time'):
                        timestamp = i['created_time']

                    if i.get('name'):
                        title = i['name']

                    if i.get('link'):
                        link = i['link']

                    if i.get('likes'):
                        likes = i['likes']['count']
                    if i.get('comments'):
                        comments = i['comments']['count']
                    if i.get('picture'):
                        picture = i['picture']

                    entry = [title.replace('\r', ''),
                    link, post_type, likes, comments,
                    picture, message.replace('\r', ''), timestamp]

                    if entry in out:
                        pass

                    else:
                        out.append(entry)

            except:
                pass

            from operator import itemgetter
            out.sort(key=itemgetter(7), reverse=True)
            return out

        root.clear_widgets()
        content = GridLayout(cols=1, spacing=0)

        items = parsefbfile()

        for i in items:

            cmnts = ''
            if int(i[4]) > 0:
                cmnts = ", comments: " + str(i[4])

            lks = ''
            if int(i[3]) > 0:
                lks = ", likes: " + str(i[3])

            btntext = "%s[size=14]\n%s\n%s, %s%s%s[/size]" % \
                (i[0].replace(' - ROBE lighting', '').
                replace('ROBE lighting - ', ''),
                i[6][0:30], i[7][0:10] + " " + i[7][11:16], i[2], lks, cmnts)

            btn = Button(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                halign='center', text_size=(Window.width - 20, None),
                markup=True)
            btn.text = btntext
            btn.bind(on_press=lambda widget, items=i[1]: self.openweb(items))
            pic_src = i[5]

            imageweb = AsyncImage(source=pic_src, size_hint=(0, 0),
                pos_hint={'x': .008, 'y': .05}, allow_stretch=False)

            wid = FloatLayout(size_hint_y=None, size=(Window.width, 110))

            wid.add_widget(btn)

            if pic_src != '':
                pass
                wid.add_widget(imageweb)

            content.add_widget(wid)
        root.add_widget(content)

    def build(self):
        self.getfbfile()
        msgbtn = Button(text='Edit source code'
        ' to add your Facebook developer credentials')
        root.add_widget(msgbtn)
        return root

if __name__ == '__main__':
                TestApp().run()
