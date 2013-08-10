from kivy.app import App
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemButton
from kivy.uix.widget import Widget
from kivy.lang import Builder


girl_names_2012_usa = ['Sophia', 'Emma', 'Isabella', 'Olivia', 'Ava', 'Emily', 'Abigail', 'Mia', 'Madison', 'Elizabeth', 'Chloe', 'Ella', 'Avery', 'Addison', 'Aubrey', 'Lily', 'Natalie', 'Sofia', 'Charlotte', 'Zoey', 'Grace', 'Hannah', 'Amelia', 'Harper', 'Lillian', 'Samantha', 'Evelyn', 'Victoria', 'Brooklyn', 'Zoe', 'Layla', 'Hailey', 'Leah', 'Kaylee', 'Anna', 'Aaliyah', 'Gabriella', 'Allison', 'Nevaeh', 'Alexis', 'Audrey', 'Savannah', 'Sarah', 'Alyssa', 'Claire', 'Taylor', 'Riley', 'Camila', 'Arianna', 'Ashley', 'Brianna', 'Sophie', 'Peyton', 'Bella', 'Khloe', 'Genesis', 'Alexa', 'Serenity', 'Kylie', 'Aubree', 'Scarlett', 'Stella', 'Maya', 'Katherine', 'Julia', 'Lucy', 'Madelyn', 'Autumn', 'Makayla', 'Kayla', 'Mackenzie', 'Lauren', 'Gianna', 'Ariana', 'Faith', 'Alexandra', 'Melanie', 'Sydney', 'Bailey', 'Caroline', 'Naomi', 'Morgan', 'Kennedy', 'Ellie', 'Jasmine', 'Eva', 'Skylar', 'Kimberly', 'Violet', 'Molly', 'Aria', 'Jocelyn', 'Trinity', 'London', 'Lydia', 'Madeline', 'Reagan', 'Piper', 'Andrea', 'Annabelle', 'Maria', 'Brooke', 'Payton', 'Paisley', 'Paige', 'Ruby', 'Nora', 'Mariah', 'Rylee', 'Lilly', 'Brielle', 'Jade', 'Destiny', 'Nicole', 'Mila', 'Kendall', 'Liliana', 'Kaitlyn', 'Natalia', 'Sadie', 'Jordyn', 'Vanessa', 'Mary', 'Mya', 'Penelope', 'Isabelle', 'Alice', 'Reese', 'Gabrielle', 'Hadley', 'Katelyn', 'Angelina', 'Rachel', 'Isabel', 'Eleanor', 'Clara', 'Brooklynn', 'Jessica', 'Elena', 'Aliyah', 'Vivian', 'Laila', 'Sara', 'Amy', 'Eliana', 'Lyla', 'Juliana', 'Valeria', 'Adriana', 'Makenzie', 'Elise', 'Mckenzie', 'Quinn', 'Delilah', 'Cora', 'Kylee', 'Rebecca', 'Gracie', 'Izabella', 'Josephine', 'Alaina', 'Michelle', 'Jennifer', 'Eden', 'Valentina', 'Aurora', 'Catherine', 'Stephanie', 'Valerie', 'Jayla', 'Willow', 'Daisy', 'Alana', 'Melody', 'Hazel', 'Summer', 'Melissa', 'Margaret', 'Kinsley', 'Kinley', 'Ariel', 'Lila', 'Giselle', 'Ryleigh', 'Haley', 'Julianna', 'Ivy', 'Alivia', 'Brynn', 'Keira', 'Daniela', 'Aniyah', 'Angela', 'Kate', 'Londyn', 'Hayden', 'Harmony', 'Adalyn', 'Megan', 'Allie', 'Gabriela', 'Alayna', 'Presley', 'Jenna', 'Alexandria', 'Ashlyn', 'Adrianna', 'Jada', 'Fiona', 'Norah', 'Emery', 'Maci', 'Miranda', 'Ximena', 'Amaya', 'Cecilia', 'Ana', 'Shelby', 'Katie', 'Hope', 'Callie', 'Jordan', 'Luna', 'Leilani', 'Eliza', 'Mckenna', 'Angel', 'Genevieve', 'Makenna', 'Isla', 'Lola', 'Danielle', 'Chelsea', 'Leila', 'Tessa', 'Adelyn', 'Camille', 'Mikayla', 'Adeline', 'Adalynn', 'Sienna', 'Esther', 'Jacqueline', 'Emerson', 'Arabella', 'Maggie', 'Athena', 'Lucia', 'Lexi', 'Ayla', 'Diana', 'Alexia', 'Juliet', 'Josie', 'Allyson', 'Addyson', 'Delaney', 'Teagan', 'Marley', 'Amber', 'Rose', 'Erin', 'Leslie', 'Kayleigh', 'Amanda', 'Kathryn', 'Kelsey', 'Emilia', 'Alina', 'Kenzie', 'Kaydence', 'Alicia', 'Alison', 'Paris', 'Sabrina', 'Ashlynn', 'Lilliana', 'Sierra', 'Cassidy', 'Laura', 'Alondra', 'Iris', 'Kyla', 'Christina', 'Carly', 'Jillian', 'Madilyn', 'Kyleigh', 'Madeleine', 'Cadence', 'Nina', 'Evangeline', 'Nadia', 'Raegan', 'Lyric', 'Giuliana', 'Briana', 'Georgia', 'Yaretzi', 'Elliana', 'Haylee', 'Fatima', 'Phoebe', 'Selena', 'Charlie', 'Dakota', 'Annabella', 'Abby', 'Daniella', 'Juliette', 'Lilah', 'Bianca', 'Mariana', 'Miriam', 'Parker', 'Veronica', 'Gemma', 'Noelle', 'Cheyenne', 'Marissa', 'Heaven', 'Vivienne', 'Brynlee', 'Joanna', 'Mallory', 'Aubrie', 'Journey', 'Nyla', 'Cali', 'Tatum', 'Carmen', 'Gia', 'Jazmine', 'Heidi', 'Miley', 'Baylee', 'Elaina', 'Macy', 'Ainsley', 'Jane', 'Raelynn', 'Anastasia', 'Adelaide', 'Ruth', 'Camryn', 'Kiara', 'Alessandra', 'Hanna', 'Finley', 'Maddison', 'Lia', 'Bethany', 'Karen', 'Kelly', 'Malia', 'Jazmin', 'Jayda', 'Esmeralda', 'Kira', 'Lena', 'Kamryn', 'Kamila', 'Karina', 'Eloise', 'Kara', 'Elisa', 'Rylie', 'Olive', 'Nayeli', 'Tiffany', 'Macie', 'Skyler', 'Addisyn', 'Angelica', 'Briella', 'Fernanda', 'Annie', 'Maliyah', 'Amiyah', 'Jayden', 'Charlee', 'Caitlyn', 'Elle', 'Crystal', 'Julie', 'Imani', 'Kendra', 'Talia', 'Angelique', 'Jazlyn', 'Guadalupe', 'Alejandra', 'Emely', 'Lucille', 'Anya', 'April', 'Elsie', 'Madelynn', 'Myla', 'Julissa', 'Scarlet', 'Helen', 'Breanna', 'Kyra', 'Madisyn', 'Rosalie', 'Brittany', 'Brylee', 'Jayleen', 'Arielle', 'Karla', 'Kailey', 'Arya', 'Sarai', 'Harley', 'Miracle', 'Kaelyn', 'Kali', 'Cynthia', 'Daphne', 'Aleah', 'Caitlin', 'Cassandra', 'Holly', 'Janelle', 'Marilyn', 'Katelynn', 'Kaylie', 'Itzel', 'Carolina', 'Bristol', 'Haven', 'Michaela', 'Monica', 'June', 'Janiyah', 'Camilla', 'Jamie', 'Rebekah', 'Audrina', 'Dayana', 'Lana', 'Serena', 'Tiana', 'Nylah', 'Braelyn', 'Savanna', 'Skye', 'Raelyn', 'Madalyn', 'Sasha', 'Perla', 'Bridget', 'Aniya', 'Rowan', 'Logan', 'Mckinley', 'Averie', 'Jaylah', 'Aylin', 'Joselyn', 'Nia', 'Hayley', 'Lilian', 'Adelynn', 'Jaliyah', 'Kassidy', 'Kaylin', 'Kadence', 'Celeste', 'Jaelyn', 'Zariah', 'Tatiana', 'Jimena', 'Lilyana', 'Anaya', 'Catalina', 'Viviana', 'Cataleya', 'Sloane', 'Courtney', 'Johanna', 'Amari', 'Melany', 'Anabelle', 'Francesca', 'Ada', 'Alanna', 'Priscilla', 'Danna', 'Angie', 'Kailyn', 'Lacey', 'Sage', 'Lillie', 'Brinley', 'Caylee', 'Joy', 'Kenley', 'Vera', 'Bailee', 'Amira', 'Aileen', 'Aspen', 'Emmalyn', 'Erica', 'Gracelyn', 'Kennedi', 'Skyla', 'Annalise', 'Danica', 'Dylan', 'Kiley', 'Gwendolyn', 'Jasmin', 'Lauryn', 'Aleena', 'Justice', 'Annabel', 'Tenley', 'Dahlia', 'Gloria', 'Lexie', 'Lindsey', 'Hallie', 'Sylvia', 'Elyse', 'Annika', 'Maeve', 'Marlee', 'Aryanna', 'Kenya', 'Lorelei', 'Selah', 'Kaliyah', 'Adele', 'Natasha', 'Brenda', 'Erika', 'Alyson', 'Braylee', 'Emilee', 'Raven', 'Ariella', 'Blakely', 'Liana', 'Jaycee', 'Sawyer', 'Anahi', 'Jaelynn', 'Elsa', 'Farrah', 'Cameron', 'Evelynn', 'Luciana', 'Zara', 'Madilynn', 'Eve', 'Kaia', 'Helena', 'Anne', 'Estrella', 'Leighton', 'Nataly', 'Whitney', 'Lainey', 'Amara', 'Anabella', 'Malaysia', 'Samara', 'Zoie', 'Amani', 'Phoenix', 'Dulce', 'Paola', 'Marie', 'Aisha', 'Harlow', 'Virginia', 'Ember', 'Regina', 'Jaylee', 'Anika', 'Ally', 'Kayden', 'Alani', 'Miah', 'Yareli', 'Journee', 'Kiera', 'Nathalie', 'Mikaela', 'Jaylynn', 'Litzy', 'Charley', 'Claudia', 'Aliya', 'Madyson', 'Cecelia', 'Liberty', 'Braelynn', 'Evie', 'Rosemary', 'Myah', 'Lizbeth', 'Giana', 'Ryan', 'Teresa', 'Ciara', 'Isis', 'Lea', 'Shayla', 'Jazlynn', 'Rosa', 'Gracelynn', 'Desiree', 'Elisabeth', 'Isabela', 'Arely', 'Mariam', 'Abbigail', 'Emersyn', 'Brenna', 'Kaylynn', 'Nova', 'Raquel', 'Dana', 'Laney', 'Laylah', 'Siena', 'Amelie', 'Clarissa', 'Lilianna', 'Lylah', 'Halle', 'Madalynn', 'Maleah', 'Sherlyn', 'Linda', 'Shiloh', 'Jessie', 'Kenia', 'Greta', 'Marina', 'Melina', 'Amiya', 'Bria', 'Natalee', 'Sariah', 'Mollie', 'Nancy', 'Christine', 'Felicity', 'Zuri', 'Irene', 'Simone', 'Amya', 'Matilda', 'Colette', 'Kristen', 'Paityn', 'Alayah', 'Janiya', 'Kallie', 'Mira', 'Hailee', 'Kathleen', 'Meredith', 'Janessa', 'Noemi', 'Aiyana', 'Aliana', 'Leia', 'Mariyah', 'Tori', 'Alissa', 'Ivanna', 'Joslyn', 'Sandra', 'Maryam', 'Saniyah', 'Kassandra', 'Danika', 'Denise', 'Jemma', 'River', 'Charleigh', 'Emelia', 'Kristina', 'Armani', 'Beatrice', 'Jaylene', 'Karlee', 'Blake', 'Cara', 'Addilyn', 'Amina', 'Ansley', 'Kaitlynn', 'Iliana', 'Mckayla', 'Adelina', 'Briley', 'Elaine', 'Lailah', 'Mercedes', 'Chaya', 'Lindsay', 'Hattie', 'Lisa', 'Marisol', 'Patricia', 'Bryanna', 'Taliyah', 'Adrienne', 'Emmy', 'Millie', 'Paislee', 'Charli', 'Kourtney', 'Leyla', 'Maia', 'Willa', 'Milan', 'Paula', 'Ayleen', 'Clare', 'Kensley', 'Reyna', 'Martha', 'Adley', 'Elianna', 'Emilie', 'Karsyn', 'Yasmin', 'Lorelai', 'Amirah', 'Aryana', 'Livia', 'Alena', 'Kiana', 'Celia', 'Kailee', 'Rylan', 'Ellen', 'Galilea', 'Kynlee', 'Leanna', 'Renata', 'Mae', 'Ayanna', 'Chanel', 'Lesly', 'Cindy', 'Carla', 'Pearl', 'Jaylin', 'Kimora', 'Angeline', 'Carlee', 'Aubri', 'Edith', 'Alia', 'Frances', 'Corinne', 'Jocelynn', 'Cherish', 'Wendy', 'Carolyn', 'Lina', 'Tabitha', 'Winter', 'Abril', 'Bryn', 'Jolie', 'Yaritza', 'Casey', 'Zion', 'Lillianna', 'Jordynn', 'Zariyah', 'Audriana', 'Jayde', 'Jaida', 'Salma', 'Diamond', 'Malaya', 'Kimber', 'Ryann', 'Abbie', 'Paloma', 'Destinee', 'Kaleigh', 'Asia', 'Demi', 'Yamileth', 'Deborah', 'Elin', 'Kaiya', 'Mara', 'Averi', 'Nola', 'Tara', 'Taryn', 'Emmalee', 'Aubrianna', 'Janae', 'Kyndall', 'Jewel', 'Zaniyah', 'Kaya', 'Sonia', 'Alaya', 'Heather', 'Nathaly', 'Shannon', 'Ariah', 'Avah', 'Giada', 'Lilith', 'Samiyah', 'Sharon', 'Coraline', 'Eileen', 'Julianne', 'Milania', 'Chana', 'Regan', 'Krystal', 'Rihanna', 'Sidney', 'Hadassah', 'Macey', 'Mina', 'Paulina', 'Rayne', 'Kaitlin', 'Maritza', 'Susan', 'Raina', 'Hana', 'Keyla', 'Temperance', 'Aimee', 'Alisson', 'Charlize', 'Kendal', 'Lara', 'Roselyn', 'Alannah', 'Alma', 'Dixie', 'Larissa', 'Patience', 'Taraji', 'Sky', 'Zaria', 'Aleigha', 'Alyvia', 'Aviana', 'Bryleigh', 'Elliot', 'Jenny', 'Luz', 'Ali', 'Alisha', 'Ayana', 'Campbell', 'Karis', 'Lilyanna', 'Azaria', 'Blair', 'Micah', 'Moriah', 'Myra', 'Lilia', 'Aliza', 'Giovanna', 'Karissa', 'Saniya', 'Emory', 'Estella', 'Juniper', 'Kairi', 'Kenna', 'Meghan', 'Abrielle', 'Elissa', 'Rachael', 'Emmaline', 'Jolene', 'Joyce', 'Britney', 'Carlie', 'Haylie', 'Judith', 'Renee', 'Saanvi', 'Yesenia', 'Barbara', 'Dallas', 'Jaqueline', 'Karma', 'America', 'Sariyah', 'Azalea', 'Everly', 'Ingrid', 'Lillyana', 'Emmalynn', 'Marianna', 'Brisa', 'Kaelynn', 'Leona', 'Libby', 'Deanna', 'Mattie', 'Miya', 'Kai', 'Annalee', 'Nahla', 'Dorothy', 'Kaylyn', 'Rayna', 'Araceli', 'Cambria', 'Evalyn', 'Haleigh', 'Thalia', 'Jakayla', 'Maliah', 'Saige', 'Avianna', 'Charity', 'Kaylen', 'Raylee', 'Tamia', 'Aubrielle', 'Bayleigh', 'Carley', 'Kailynn', 'Katrina', 'Belen', 'Karlie', 'Natalya', 'Alaysia', 'Celine', 'Milana', 'Monroe', 'Estelle', 'Meadow', 'Audrianna', 'Cristina', 'Harlee', 'Jazzlyn', 'Scarlette', 'Zahra', 'Akira', 'Ann', 'Collins', 'Kendyl', 'Anabel', 'Azariah', 'Carissa', 'Milena', 'Tia', 'Alisa', 'Bree', 'Carleigh', 'Cheyanne', 'Sarahi', 'Laurel', 'Kylah', 'Tinley', 'Kora', 'Marisa', 'Esme', 'Sloan', 'Cailyn', 'Gisselle', 'Kasey', 'Kyndal', 'Marlene', 'Riya', 'Annabell', 'Aubriana', 'Izabelle', 'Kirsten', 'Aya', 'Dalilah', 'Devyn', 'Geraldine', 'Analia', 'Hayleigh', 'Landry', 'Sofie', 'Tess', 'Ashtyn', 'Jessa',
'Katalina']


Builder.load_string('''
<ScrollTestView>:
    list_view: list_view

    BoxLayout:
        size: self.size
        orientation: 'vertical'

        Button:
            text: 'scroll_to_first()'
            on_release: root.list_view.scroll_to_first()

        Button:
            text: 'scroll_to_last()'
            on_release: root.list_view.scroll_to_last()

        Button:
            text: 'scroll_by(-100)'
            on_release: root.list_view.scroll_by(-100)

        Button:
            text: 'scroll_by(-10)'
            on_release: root.list_view.scroll_by(-10)

        Button:
            text: 'scroll_by(10)'
            on_release: root.list_view.scroll_by(10)

        Button:
            text: 'scroll_by(100)'
            on_release: root.list_view.scroll_by(100)

        Button:
            text: 'scroll_to(500)'
            on_release: root.list_view.scroll_to(500)

        Button:
            text: 'scroll_to_selection()'
            on_release: root.list_view.scroll_to_selection()

        Button:
            text: 'scroll_to_first_selected()'
            on_release: root.list_view.scroll_to_first_selected()

        Button:
            text: 'scroll_to_last_selected()'
            on_release: root.list_view.scroll_to_last_selected()

    ListView:
        id: list_view
        size: self.size
        adapter: app.us_baby_girl_names_2012
''')


class ScrollTestView(BoxLayout):
    pass


class ScrollTestApp(App):

    def __init__(self, **kwargs):
        super(ScrollTestApp, self).__init__(**kwargs)

        list_item_args_converter = \
                lambda row_index, name: {'text': name,
                                        'size_hint_y': None,
                                        'height': 25}

        self.us_baby_girl_names_2012 = \
                ListAdapter(
                    data=girl_names_2012_usa,
                    args_converter=list_item_args_converter,
                    selection_mode='multiple',
                    allow_empty_selection=False,
                    cls=ListItemButton)

    def build(self):

        return ScrollTestView()

if __name__ in ('__main__'):
    ScrollTestApp().run()
