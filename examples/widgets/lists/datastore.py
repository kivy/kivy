# ----------------------------------------------------------------------------
#
# Simulate a datastore for an app.
#
# In a system of models for this sample fruit data, we would have two record
# types, category and fruit, with category having a to_many relationship to
# fruit and with fruit having a to_one relationship to category. 
#
# In ListAdapter and the system or related classes, we sync selection in the
# user interface to selection of datastore, datarecord properties. In the
# datastore treatment here, we use dictionaries for the data, but we could just
# as well define the attributes of the following DataModel stubs and used
# instances of them in a simulated database:
#
# class DataModel(object):
#     pass
#
#
# class FruitCategoryRecord(DataModel):
#     pass
#
#
# class FruitRecord(DataModel):
#     pass
#
#
# The DataStore below does not use such classes as FruitCategoryRecord and
# FruitRecord. It uses dictionaries.

from kivy.properties import StringProperty, DictProperty


class DataStore(object):

    def __init__(self, name, db_dict):
        self.name = name
        self.db_dict = db_dict

    def set(self, key, prop, val):
        if key in self.db_dict:
            if prop in self.db_dict[key]:
                self.db_dict[key][prop] = val
                return
            msg = "DataStore {0} set: no property {1} in record[{2}]".format(
                    self.name, prop, key)
            raise Exception(msg)
        msg = "DataStore {0} set: unknown record for key: {1}".format(
                self.name, key)
        raise Exception(msg)

    def get(self, key, prop):
        if key in self.db_dict:
            if prop in self.db_dict[key]:
                return self.db_dict[key][prop]
            msg = "DataStore {0} get: no property {1} in record[{2}]".format(
                    self.name, prop, key)
            raise Exception(msg)
        msg = "DataStore {0} get: unknown record for key: {1}".format(
                self.name, key)
        raise Exception(msg)
        return None


# NOTE: When creating a datastore system for your app, you could create classes
#       like the ones stubbed out above, intead of relying on dictionaries. You
#       could also put the raw data in JSON, and create an interface. However
#       it is done, to work with the ListAdapter and selection system, the
#       data models need to include is_selected somehow.
#
#       In fruits example data, all fruit category keys and fruit keys are
#       unique, so they work as record ids. However, for your work, you may
#       wish to have record ids as keys.
