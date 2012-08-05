from datastore import DataStore

integers_dict = \
        {str(index): {'is_selected': False} for index in xrange(100)}

datastore_integers = DataStore(name='integers', db_dict=integers_dict)
