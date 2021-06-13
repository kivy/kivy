import datetime, re
from random import sample, randint
from string import ascii_lowercase

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

kv = """
#: import Clock kivy.clock.Clock
<PopupLabelCell>
    size_hint: (None, None)
    height: 30
    text_size: self.size
    halign: "right"
    valign: "middle"

<EditStatePopup>:
    container: container
    size_hint: None, None
    size: 400, 300
    title_size: 20
    auto_dismiss: True

    BoxLayout:
        orientation: "vertical"
        padding: dp(10)    
        
        GridLayout:
            id: container
            cols: 2
            row_default_height: 30
            cols_minimum: {0: 100, 1: 220}
            size_hint: (None, None)
            height: self.minimum_height
            padding: dp (10)
            spacing: dp (5)
            PopupLabelCell:
                text: 'Date'
            GridLayout:
                cols:3 
                Spinner:
                    id: DD                    
                Spinner:
                    id: MM
                    values: ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
                Spinner:
                    id: YY
                    values: ('2020','2021','2022','2023','2024','2025','2026','2027','2028')
            PopupLabelCell:
                text: 'Customer'
            TextInput:
                id: customer
                write_tab: False
                on_focus: Clock.schedule_once(lambda dt: self.select_all()) if self.focus else None
            PopupLabelCell:
                text: 'Length'
            GridLayout:
                cols: 4
                TextInput:
                    id: length
                    halign: "center"
                    valign: "middle"
                    write_tab: False
                    on_focus: Clock.schedule_once(lambda dt: self.select_all()) if self.focus else None
                Spinner:
                    id: uom
                    text: 'mm'
                    values: ('mm', 'cm', 'meter', 'inch', 'feet')
                Button:
                    text: '-'
                    on_press: length.text = str(int(length.text) - 1) if (int(length.text) - 1) > 0 else str(1)                
                Button:
                    text: '+'
                    on_press: length.text = str(int(length.text) + 1)                 
            PopupLabelCell:
                text: 'Quantity'
            GridLayout:
                cols: 4
                TextInput:
                    id: qty
                    halign: "center"
                    valign: "middle"
                    write_tab: False
                    on_focus: Clock.schedule_once(lambda dt: self.select_all()) if self.focus else None
                Label:
                    text: 'nos'
                Button:
                    text: '-'
                    on_press: qty.text = str(int(qty.text) - 1) if (int(qty.text) - 1) > 0 else str(1)                
                Button:
                    text: '+'
                    on_press: qty.text = str(int(qty.text) + 1)
            PopupLabelCell:
                text: 'Order ID'
                opacity: 0                
            TextInput:
                id: orderno
                disabled: True
                opacity: 0
                
        BoxLayout:
            Button:
                size_hint: 1, 0.5
                text: "Save Changes"
                on_release:
                    app.root.save(orderno.text, DD.text, MM.text, YY.text, customer.text, length.text, uom.text, qty.text); root.dismiss()
            Button:
                size_hint: 1, 0.5
                text: "Cancel Changes"
                on_release: app.root.remove(orderno.text); root.dismiss()

<Row@RecycleKVIDsDataViewBehavior+BoxLayout>:
    canvas.before:
        Color:
            rgba: 0.5, 0.5, 0.5, 1
        Rectangle:
            size: self.size
            pos: self.pos
    orderno: ''    
    Button:
        on_press: app.root.remove(orderno.text)
        text: 'X'
        size_hint: 0.3, 1
    Button:
        on_press: app.root.edit(orderno.text)
        text: 'Edit'
        size_hint: 0.3, 1
    Button:
        id: selectitem
        text: 'Select'
        size_hint: 0.3, 1
        on_press: print("Selected item:" + orderno.text)
    Label:
        id: orderno
        text: root.orderno      
    Label:
        id: date        
    Label:
        id: customer        
    Label:
        id: qty    
<OrderHandler>:    
    canvas:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        Rectangle:
            size: self.size
            pos: self.pos
    rv: rv
    orientation: 'vertical'
    GridLayout:
        cols: 6
        rows: 1
        size_hint_y: None
        height: dp(54)
        padding: dp(8)
        spacing: dp(16)
        Button:
            text: 'New Order..'
            on_press: root.add()
        Button:
            text: 'Sort by Order ID'
            on_press: root.sort('orderno')        
        Button:
            text: 'Sort by Date'
            on_press: root.sort('date')            
        Button:
            text: 'Sort by Customer'
            on_press: root.sort('customer')
        Button:
            text: 'Clear'
            size_hint: 0.7, 1            
            on_press: root.clear()        
        Button:
            text: 'Exit'
            size_hint: 0.5, 1
            on_press: app.stop()
        

    RecycleView:
        id: rv
        scroll_type: ['bars', 'content']
        scroll_wheel_distance: dp(114)
        bar_width: dp(10)
        viewclass: 'Row'
        RecycleBoxLayout:
            default_size: None, dp(60)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            spacing: dp(3)
"""

Builder.load_string(kv)

class PopupLabelCell(Label):
    pass

class EditStatePopup(Popup):

    def __init__(self, order, **kwargs):
        super(EditStatePopup, self).__init__(title='Order ID #' + order['orderno'] , **kwargs)
        self.populate_content(order)

    def populate_content(self, order):
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        self.ids.orderno.text = str(order['orderno'])
        if(order['date.text']):
            self.ids.DD.text = str(order['date.text']).split('-')[0]
            self.ids.DD.values = [str(dd) for dd in range(1,32,1)]
            self.ids.MM.text = str(order['date.text']).split('-')[1]
            self.ids.MM.values = months
            self.ids.YY.text = str(order['date.text']).split('-')[2]
            self.ids.YY.values = [str(yy) for yy in range(2020,2031,1)] 
        if(order['customer.text']):
            self.ids.customer.text = str(order['customer.text'])
        if(order['qty.text']):
            self.ids.length.text = "".join(re.findall("[0-9]+", str(order['qty.text'].split('x')[0])))
            self.ids.uom.text = "".join(re.findall("[a-zA-Z]+", str(order['qty.text'].split('x')[0])))
            self.ids.qty.text = "".join(re.findall("[0-9]+", str(order['qty.text'].split('x')[1])))
    
class OrderHandler(BoxLayout):

    sorted_customer = False
    sorted_orderno = False
    sorted_date = False
    
    def __init__(self, **kwargs):
        super(OrderHandler, self).__init__(**kwargs)
        self.populate_random()        
        self.sort('orderno')
        self.sort('orderno')
    
    def populate_random(self):
        self.rv.data = [
            {'date.text': ''.join((datetime.date.today() - datetime.timedelta(days=randint(0,30))).strftime('%d-%b-%Y')),
             'customer.text': ''.join(sample(ascii_lowercase, 6)),
             'orderno':str(x+1),
             'qty.text': str(randint(1,100)) + 'mm x ' + str(randint(1,50)) + 'nos' }             
            for x in range(50)]

    def sort(self, key):        
        if key == 'customer':
            self.rv.data = sorted(self.rv.data, key=lambda x: x['customer.text'], reverse = self.sorted_customer)
            self.sorted_customer = not self.sorted_customer
        elif key == 'orderno':
            self.rv.data = sorted(self.rv.data, key=lambda x: int(x['orderno']), reverse = self.sorted_orderno)
            self.sorted_orderno = not self.sorted_orderno
        elif key == 'date':
            self.rv.data = sorted(self.rv.data, key=lambda x: x['date.text'], reverse = self.sorted_date)
            self.sorted_date = not self.sorted_date

    def clear(self):
        self.rv.data = []

    def add(self):
        if self.rv.data:
            if (self.sorted_orderno):
                self.sort('orderno')
            else: 
                self.sort('orderno')
                self.sort('orderno')
            
            lastorderno = self.rv.data[0].get('orderno')    
            print("Last order number:" + lastorderno)
        else:
            lastorderno = 0
        
        self.rv.data.insert(0, 
            {'date.text': ''.join(datetime.date.today().strftime('%d-%b-%Y')),
             'customer.text': '',
             'orderno':str(int(lastorderno)+1),
             'qty.text': '10mm x 1nos' })
        
        self.edit(int(lastorderno)+1)

    def update(self, value):
        if self.rv.data:
            self.rv.refresh_from_data()
            
    def edit(self, id):
        if self.rv.data:
            list = self.rv.data.copy()            
            list[:] = [d for d in list if d.get('orderno') == str(id)]
            print("Editing order: " + str(list[0]))
            if (list[0]):
                popup = EditStatePopup(list[0])
                popup.open()            
            
    def save(self, orderno, DD, MM, YY, customer, length, uom, qty): 
        if self.rv.data:
            print ("Adding order: " + orderno + " |  " + DD + "-" + MM  + "-" + YY + " | " + customer  + " | " + length +  uom  + " x " + qty + "nos")
            self.remove(orderno)
            self.rv.data.insert(0,
                {'date.text': DD + "-" + MM + "-" + YY,
                 'customer.text': customer.strip(),
                 'orderno': str(orderno),
                 'qty.text': length.strip() + uom + " x " + qty.strip() + "nos"})        
            self.rv.refresh_from_data()
            
    def remove(self, id):        
        if self.rv.data:
            print ("Removing Order id... " + str(id))
            list = self.rv.data.copy()            
            list[:] = [d for d in list if d.get('orderno') != str(id)]
            self.rv.data = list
            self.rv.refresh_from_data()
            

class OrderHandlerApp(App):
    def build(self):
        return OrderHandler()

if __name__ == '__main__':
    OrderHandlerApp().run()
