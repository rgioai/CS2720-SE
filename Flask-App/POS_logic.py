"""
Author: Ethan Morisette; Ryan Giarusso
Created: 3/1/2016
Purpose: module that holds all class definitions, function definitions, and variables for displaying information
to the WEBSITE tables (not to be confused with our db tables)
"""

#######################################################################################################################
#  IMPORTS
#######################################################################################################################
from flask import *


#######################################################################################################################
#  CLASS DEFINITIONS
#######################################################################################################################
class Row:
    """
    Parent class for specialized rows.
    """
    def __init__(self):
        self.data = ""


class UserRow(Row):
    def __init__(self, user_id, username, password, permissions):
        """
        Holds data for the display of an entry from the users database table.
        :param user_id: int
        :param username: str
        :param password: str
        :param permissions: int
        :return: None
        """
        Row.__init__(self)
        self.user_id = user_id
        self.username = username
        self.password = password
        self.permissions = permissions


class SupplierRow(Row):
    def __init__(self, supplier_id, name, email):
        """
        Holds data for the display of an entry from the suppliers database table.
        :param supplier_id: int
        :param name: str
        :param email: str
        :return:
        """
        Row.__init__(self)
        self.supplier_id = supplier_id
        self.name = name
        self.email = email


class ProductsRow(Row):

    def __init__(self, product_id, name, supplier_id,
                 inventory_count, min_inventory, shelf_life, standard_price):
        """
        Holds data for the display of an entry from the products database table.
        :param product_id: int
        :param name: str
        :param supplier_id: int
        :param inventory_count: int
        :param min_inventory: int
        :param shelf_life: int
        :param standard_price: float
        :return: None
        """
        Row.__init__(self)
        self.product_id = product_id
        self.name = name
        self.supplier_id = supplier_id
        self.inventory_count = inventory_count
        self.min_inventory = min_inventory
        self.shelf_life = shelf_life
        self.standard_price = standard_price


class ItemRow(Row):
    def __init__(self, item_id, product_id, inventory_cost, expiration_date):
        """
        Holds data for the display of an entry from the items database table.
        :param item_id: int
        :param product_id: int
        :param inventory_cost: float
        :param expiration_date: datetime.date
        :return: None
        """
        Row.__init__(self)
        self.item_id = item_id
        self.product_id = product_id
        self.inventory_cost = inventory_cost
        self.expiration_date = expiration_date


class ItemSoldRow(Row):
    def __init__(self, item_sold_id, item_id, product_id, price_sold, inventory_cost, transaction_id):
        """
        Holds data for the display of an entry from the items_sold database table.
        :param item_sold_id: int
        :param item_id: int
        :param product_id: int
        :param price_sold: float
        :param inventory_cost: float
        :param transaction_id: int
        :return: None
        """
        Row.__init__(self)
        self.item_sold_id = item_sold_id
        self.item_id = item_id
        self.product_id = product_id
        self.price_sold = price_sold
        self.inventory_cost = inventory_cost
        self.transaction_id = transaction_id


class DiscountRow(Row):
    def __init__(self, discount_id, product_id, start_date, end_date, discount):
        """
        Holds data for the display of an entry from the discounts database table.
        :param discount_id: int
        :param product_id: int
        :param start_date: datetime.date
        :param end_date: datetime.date
        :param discount: float (percentage off)
        :return: None
        """
        Row.__init__(self)
        self.discount_id = discount_id
        self.product_id = product_id
        self.start_date = start_date
        self.end_date = end_date
        self.discount = discount


class TransactionRow(Row):
    def __init__(self, trans_id, cust_name, cust_contact, payment_type, date):
        """
        Holds data for the display of an entry from the transactions database table.
        :param trans_id: int
        :param cust_name: str
        :param cust_contact: str
        :param payment_type: int
        :param date: datetime.date
        :return: None
        """
        Row.__init__(self)
        self.trans_id = trans_id
        self.cust_name = cust_name
        self.cust_contact = cust_contact
        self.payment_type = payment_type
        self.date = date


class CashierRow(Row):
    def __init__(self, item_id, product_name, price):
        """
        Holds data for the display of an item in a customer's cart currently checking out.
        :param item_id: int
        :param product_name: str
        :param price: float
        :return: None
        """
        Row.__init__(self)
        self.item_id = item_id
        self.product_name = product_name
        self.price = price


class StockerRow(ItemRow):
    def __init__(self, product_id, name, inventory_cost):
        """
        Holds data for the display of an item currently being added to inventory.
        :param product_id: int
        :param inventory_cost: float
        :return: None
        """
        Row.__init__(self)
        self.product_id = product_id
        self.name = name
        self.inventory_cost = inventory_cost


class Table:
    """
    Purpose: to hold a variety of table information beyond the rows themselves (e.g. table rows, potential profit from
    all items currently in the table, etc.)
    """
    def __init__(self):
        self.rowsList = []  # list of row objects (receiptRow, stockRow, or saleRow)
        self.rowCount = 0  # integer
        self.mostRecentRow = None  # row object (receiptRow, stockRow, or saleRow)


class CashierTable(Table):

    def add_row(self, item_id, product_name, price):
        """
        Adds a cashier row to the cashier table.
        :param item_id: int
        :param product_name: str
        :param price: float
        :return: None
        """
        new_row = CashierRow(item_id, product_name, price)
        self.rowsList.append(new_row)
        self.rowCount += 1
        self.mostRecentRow = new_row

    def edit_row(self, row_number, item_id, product_name, price):
        """
        Changes a current row at index row_number-1 to the parameters specified.
        If any row parameter is the empty string, it will default to its current setting.
        :param row_number: int
        :param item_id: int
        :param product_name: str
        :param price: float
        :return:
        """
        if item_id == '':
            item_id = self.rowsList[row_number-1].item_id
        if product_name == '':
            product_name = self.rowsList[row_number-1].product_name
        if price == '':
            price = self.rowsList[row_number-1].price
        self.rowsList[row_number-1] = CashierRow(item_id, product_name, price)

    def clear_table(self):
        """
        Clear all contents of a display table. Intended for use after a batch of data is committed to the database.
        :return: None
        """
        self.rowsList.clear()
        self.rowCount = 0
        self.mostRecentRow = None

    def delete_row(self, row_number):
        """
        Deletes the row at index row_number-1
        :param row_number: int
        :return: None
        """
        self.rowsList.pop(row_number-1)


class StockerTable(Table):

    def add_row(self, product_id, inventory_cost):
        """
        Adds a stocker row to the stocker table.
        :param product_id: int
        :param inventory_cost: float
        :return: None
        """
        new_row = StockerRow(product_id, inventory_cost)
        self.rowsList.append(new_row)
        self.rowCount += 1
        self.mostRecentRow = new_row

    def edit_row(self, row_number, product_id, inventory_cost):
        """
        Changes a current row at index row_number-1 to the parameters specified.
        If any row parameter is the empty string, it will default to its current setting.
        :param row_number: int
        :param product_id: int
        :param inventory_cost: float
        :return: None
        """
        if product_id == '':
            product_id = self.rowsList[row_number-1].item_id
        if inventory_cost == '':
            inventory_cost = self.rowsList[row_number-1].product_name
        self.rowsList[row_number-1] = StockerRow(product_id, inventory_cost)

    def clear_table(self):
        """
        Clear all contents of a display table. Intended for use after a batch of data is committed to the database.
        :return: None
        """
        self.rowsList.clear()
        self.rowCount = 0
        self.mostRecentRow = None

    def delete_row(self, row_number):
        """
        Deletes the row at index row_number-1
        :param row_number: int
        :return: None
        """
        self.rowsList.pop(row_number-1)


#######################################################################################################################
# GLOBAL VARIABLES
#######################################################################################################################

"""
# Tables for editors
users_table = Table()
suppliers_table = Table()
products_table = Table()
items_table = Table()
items_sold_table = Table()
discounts_table = Table()
transactions_table = Table()
"""

# Tables for cashier/stocker
cashier_table = CashierTable()
stocker_table = StockerTable()

######################################################################################################################
# FUNCTION DEFINITIONS
######################################################################################################################
