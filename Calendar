from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
import calendar
from datetime import date
from kivy.properties import StringProperty

'''
Joseph Aferzon MD
Connecticut Spine Institute for Minimally Invasive Surgery
Department of Neurosurgery
Hartford Hospital
CSIMIS.com
'''
    
class Update_buts():
   '''
   Recieves arb= array of calendar buttons and date to select
   lables each button appropriately by calculating monthly spread
   Left is as a class in case incorporate different calendars
   s.a. Roman, Hebrew ..
   '''
   def Ch_buts(self,arb,pmo,pdy,pyr):
      '''
      Assign appropriate labels to button layout
      arb=array of button instances
      pmo,pdy,pyr = date to open with
      '''
      arb[len(arb)-3].text=str(calendar.month_abbr[pmo])
      arb[len(arb)-2].text=str(pdy)
      arb[len(arb)-1].text=str(pyr)
      dy=calendar.monthcalendar(pyr,pmo)
      tod=date.today().timetuple()
      tt=tod[2]
      if (tod[0]!= pyr) or (tod[1]!= pmo):
         tt=100
      amo=pmo+1;ayr=pyr
      bmo=pmo-1;byr=pyr
      if (pmo==12):
         amo=1;ayr=pyr+1
      if (pmo==1):
         bmo=12;byr=pyr-1
      ay=calendar.monthcalendar(ayr,amo)
      by=calendar.monthcalendar(byr,bmo)
      for i in range(len(dy)):
         for j in range(0,7):
            arb[i*7+j].text=str(dy[i][j])
            arb[i*7+j].background_color=(1,1,1,1)
            if dy[i][j]== pdy:
               arb[i*7+j].text='[color=ff0000][b]'+str(dy[i][j])+'[/b][/color]'            
            if dy[i][j]== tt:  #FIX TODAY STAMP
               arb[i*7+j].text='[color=ffff00][b]'+str(dy[i][j])+'[/b][/color]'
      for i in range(len(dy[0])):
         if dy[0][i]==0:
            dy[0][i]=by[len(by)-1][i]
            arb[i].text=str(dy[0][i])
            arb[i].background_color=(.5,1,1,0)
      if len(dy)==5:
         if dy[len(dy)-1][6]== 0:
            dy.append(ay[1])
            for j in range(0,7):
               arb[35+j].text=str(dy[5][j])
               arb[35+j].background_color=(.5,1,1,0)   
            for i in range(0,7):
               if dy[4][i]==0:
                  dy[4][i]=ay[0][i]
                  arb[28+i].text=str(dy[4][i])
                  arb[28+i].background_color=(.5,1,1,0)
         else:
            dy.append(ay[0])
            for j in range(0,7):
               arb[35+j].text=str(dy[5][j])
               arb[35+j].background_color=(.5,1,1,0)   
      else:
         for i in range(len(dy[5])):
            if dy[5][i]==0:
               dy[5][i]=ay[0][i]
               arb[35+i].text=str(dy[5][i])
               arb[35+i].background_color=(.5,1,1,0)
  
class MLay(GridLayout):
   '''
   Draw all the buttons and controls layout
   1. Convert tMo tDay tYr into selector or
   drop-down list
   2.Get pics for nicer looking controls
   '''
   buts=[] #keeps buttons and current date(last 3), same as arb
   tday=date.today().timetuple()
   dn=['Mon','Tue','Wed','Thur','Fri','Sat','Sun']
   mn=list(calendar.month_abbr)
   def CalAct(self,evt):
      if self.dyr==0 or self.dmo==0:
         arb=self.buts
         self.dmo=list(calendar.month_abbr).index(arb[len(arb)-3].text)
         self.dyr=int(arb[len(arb)-1].text)
         self.ddy=int(arb[len(arb)-2].text)
      if evt.text=='Yr+':
         self.dyr=self.dyr+1
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
      if evt.text=='-Yr':
         self.dyr=self.dyr-1
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
      if evt.text=='Mo+':
         self.dmo=self.dmo+1
         if self.dmo == 13:
            self.dmo=1
            self.dyr=self.dyr+1
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
      if evt.text=='-Mo':
         self.dmo=self.dmo-1
         if self.dmo == 0:
            self.dmo=12
            self.dyr=self.dyr-1
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
      if evt.text=='TODAY':
         self.dmo=self.tday[1];self.dyr=self.tday[0];self.ddy=self.tday[2]
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
   def ButExit(self,evt): #Place date into appropriate tDate based on vvar
      self.parent.vvar.text=str(self.dmo)+'/'+str(self.ddy)+'/'+str(self.dyr)
      self.dyr=0;self.dmo=0
      self.parent.dismiss(force=True)
   def ButAct(self,evt): #When date layout button is pressed
      if evt.background_color==[1,1,1,1]:
         t=evt.text
         six=t.find(r'[b]')
         if six ==-1:
            self.ddy=int(evt.text)
         else:
            fix=t.find(r'[/b]')
            self.ddy=int(t[six+3:fix])
         arb=self.buts
         if self.dyr==0 or self.dmo==0:
            self.dmo=list(calendar.month_abbr).index(arb[len(arb)-3].text)
            self.dyr=int(arb[len(arb)-1].text)
         arb[len(arb)-3].text=str(calendar.month_abbr[self.dmo])
         arb[len(arb)-2].text=str(self.ddy)
         arb[len(arb)-1].text=str(self.dyr)
         Update_buts().Ch_buts(self.buts,self.dmo,self.ddy,self.dyr)
   def __init__(self,**kwargs):
      kwargs.setdefault('rows',4)
      super(MLay,self).__init__(**kwargs)
      self.dmo=0;self.ddy=0;self.dyr=0
      r1=GridLayout(cols=7,size_hint_y=None,size=(1,70))
      r2=GridLayout(cols=6,size_hint_y=None,size=(1,70))
      r3=GridLayout(cols=7,size_hint_y=None,size=(1,40))
      r4=GridLayout(cols=7,size_hint_y=None,size=(1,280))
      for ii in self.dn:
         r3.add_widget(Label(text='[b]'+ii+'[/b]' , markup=True))
      for jj in range(42):
         self.buts.append(Button(text='',markup=True))
         self.buts[jj].bind(on_press=self.ButAct)
         r4.add_widget(self.buts[jj])            
      pad1=GridLayout(cols=1)
      self.tMo=TextInput(size_hint=(None,None),size=(120,1))
      self.tDy=TextInput(size_hint=(None,None),size=(40,1))
      self.tYr=TextInput(size_hint=(None,None),size=(50,1))
      bOK=Button(text='OK',size_hint=(None,None),size=(70,1))
      bOK.bind(on_press=self.ButExit)
      bCancel=Button(text='Cancel',size_hint=(None,None),size=(70,1))
      pad2=GridLayout(cols=1)        
      bYF=Button(text='Yr+')
      bYB=Button(text='-Yr')
      bMF=Button(text='Mo+')
      bMB=Button(text='-Mo')
      bTD=Button(text='TODAY')
      bYF.bind(on_press=self.CalAct)
      bYB.bind(on_press=self.CalAct)
      bMF.bind(on_press=self.CalAct)
      bMB.bind(on_press=self.CalAct)
      bTD.bind(on_press=self.CalAct)
      self.buts.append(self.tMo)
      self.buts.append(self.tDy)
      self.buts.append(self.tYr)
   
        
      r1.add_widget(pad1);r1.add_widget(self.tMo);r1.add_widget(self.tDy)
      r1.add_widget(self.tYr);r1.add_widget(pad2);r1.add_widget(bOK)
      r1.add_widget(bCancel);
      r2.add_widget(bYB);r2.add_widget(bMB)
      r2.add_widget(bTD)
      r2.add_widget(bMF);r2.add_widget(bYF)       
      self.add_widget(r1);self.add_widget(r2);self.add_widget(r3)
      self.add_widget(r4)
class MView(ModalView):
   vvar='' #pass correct tDate if multiple simultaneous date fields.
   def __init__(self,**kwargs):
      kwargs.setdefault('size_hint',(None,None))
      kwargs.setdefault('size',(400,460))
      kwargs.setdefault('auto_dismiss',False)
      super(MView,self).__init__(**kwargs)
class DateInput(GridLayout): #need this to place tDate and bDate into calling layout
   '''
   If need to bind to change of date use DateInput()instance.tDate.bind()
   '''
   def __init__(self,bTxt,tTxt,**kwargs):
      kwargs.setdefault('cols',2)

      super(DateInput,self).__init__(**kwargs)
      self.tDate=TextInput(text='',size_hint=(None,None),size=(100,50))
      self.bDate=Button(text='',size_hint=(None,None),size=(100,50))
      self.bDate.text=bTxt
      self.tDate.text=tTxt
      self.add_widget(self.bDate);self.add_widget(self.tDate)
      self.bDate.bind(on_press=self.GetCal)

   def GetCal(self,inst): #Get and adjust date value from tDate
      self.v.vvar=self.tDate
      sd=self.tDate.text.split('/')
      diff=1900
      if int(sd[2])<15:
         diff=2000
      if int(sd[2])>99:
         diff=0
      self.dd.Ch_buts(self.cc.buts,int(sd[0]),int(sd[1]),int(sd[2])+diff)
      self.v.open()
   v=MView()
   cc=MLay()
   v.add_widget(cc)
   dd=Update_buts()
