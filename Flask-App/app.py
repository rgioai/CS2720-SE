# File : app.py
# Date : 3/11/2016 (creation)
# Desc : This is the master file for the Flask application.


#############################
# Import Statements
#############################
from flask import *
from POS_helpers import *
from templates.form import LoginForm, RegisterForm
from helper import *
from helper import login_user, login_required, logout_user
from flask.ext.bcrypt import Bcrypt
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import POS_display
import POS_logic

# -------------------------------------------------- #


#############################
# Configure the Application
#############################

# Grabs the domain name the app is running on #
app = Flask(__name__)

# Sets bcrypt for unique password hashing #
bcrypt = Bcrypt(app)

# Configure our application secret key [DO NOT CHANGE!!!]#
app.secret_key = '\xb7{\xbb\x9b\x9b\x11\xa7\\Ib\xcf\xe4\x00\x99Yi\xafg\xd2\x96\x82\x18\x18\x9d'

# Configure our database settings #

# Production Database Settings #

# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
#    username="SailingSales",
#    password="sailin123$",
#    hostname="SailingSales.mysql.pythonanywhere-services.com",
#    databasename="SailingSales$master",
# )
# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
# app.config["SQLALCHEMY_POOL_RECYCLE"] = 299

# For a local database, using SQLite, the settings would look like this, instead of what is above. so comment that out #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
# Where items.db is the created database locally #

# Setup a global instance of the database #
# use: 'from app import db' #
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Import all the database models from our 'models.py' file
# NOTE: We import down here because we have to set up the database
# (right above this) BEFORE we can import our models
# (thus it cannot go on the top of the page) #
from models import *
import POS_database

# Setup Flask Login Manager #
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Points to our "login" function "


# The magic that makes foreign keys activated in sqlite
@login_manager.user_loader
def load_user(user_id):
    global current_user
    current_user = User.query.filter(User.id == int(user_id)).first()
    return User.query.filter(User.id == int(user_id)).first()


# -------------------------------------------------- #


#############################
# Global Variables
#############################
current_user = None


#############################
# Route Declarations
#############################


# Home Route (login page) #
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    global current_user  # allows changing of the globally defined current_user #

    if request.method == 'POST':  # If the login button was clicked #
        if form.validate_on_submit():

            user = User.query.filter_by(name=request.form['username']).first()

            if user is None:
                error = "Invalid username. Please try again"
                render_template('login.html', form=form, error=error)
            else:
                if bcrypt.check_password_hash(user.password, request.form['password']):
                    login_user(user)
                    current_user = user
                    flash('You have been successfully logged in.')

                    return redirect_after_login(current_user)  # from POS_helpers #
                else:
                    error = "Username found, but invalid password. Please try again."
                    render_template('login.html', form=form, error=error)
        else:
            render_template('login.html', form=form, error=error)

    # If the form was not a submit, we just need to grab the page data (GET request) #
    return render_template('login.html', form=form, error=error)


# -------------------------------------------------- #


# Logout Route(has no page, merely a function) #
@app.route('/logout')
def logout():
    global current_user
    if current_user is None:
        flash("You are already signed out.")
        return redirect(url_for('login'))
    logout_user()
    current_user = None
    flash('You have been successfully logged out.')
    return redirect(url_for('login'))


# -------------------------------------------------- #

# Discounts Page
# Requires: Login, Manager/Admin permission #
@app.route('/discounts')
@login_required
def discounts():
    discountTable = []
    if is_manager(current_user):
        return render_template("discounts.html", discountTable=discountTable)
    else:
        return redirect('/')


@app.route('/discountsadd', methods=["POST"])
def discountsAddRow():
    # get the information from the user
    inputDict = POS_display.getDiscountRow(request)
    # get the product name from the database
    productName = POS_database.getProductName(db, inputDict["productID"])
    POS_logic.addDiscountRow(productName, inputDict["productID"], inputDict["saleStart"], inputDict["saleEnd"],
                             inputDict["salePrice"])
    return redirect(url_for('discounts'))


# -------------------------------------------------- #

# Reports Page
# Requires: Login, Manager/Admin permission #
@app.route('/reports')
@login_required
def reports():
    if is_manager(current_user):
        return render_template("reports.html")
    else:
        return redirect('/')


# -------------------------------------------------- #

# Transactions Page
# Requires: Login, Manager/Admin permission #
@app.route('/transactions')
@login_required
def transactions():
    transactionTable = []
    if is_manager(current_user) or is_cashier(current_user):
        items = db.session.query(Item).all()
        return render_template("transactions.html", items=items, transactionTable=POS_logic.cashier_table)
    else:
        return redirect('/')


@app.route('/transactionadd', methods=["POST"])
def cashierAddRow():
    # get the information from the user
    inputDict = POS_display.get_cashier_row(request)
    # get the product name and price from the database
    productID = POS_database.getItemProduct(db, inputDict["item_id"])
    productName = POS_database.getProductName(db, productID)
    pricePerUnit = POS_database.getProductPrice(db, productID)
    # add the received information to the local receipt table
    POS_logic.cashier_table.add_row(inputDict["item_id"], productName, pricePerUnit)
    return redirect(url_for('transactions'))

@app.route('/cashierdelete', methods=["POST"])
def cashierDeleteRow():
    inputDict = POS_display.get_cashier_row(request)
    POS_logic.cashier_table.delete_row(int(inputDict["row_number"]))
    return redirect(url_for('transactions'))

@app.route('/transactioncommit', methods=["POST"])
def finishTransaction():
    # TODO send all information from the local receipt table to the database for storage
    POS_database.updateCashierTable(db, POS_logic.cashier_table.rowsList)
    # clear the local receipt table out
    POS_logic.cashier_table.clear_table()
    return redirect(url_for('transactions'))

@app.route('/cashiercancel', methods=["POST"])
def cashierCancel():
    POS_logic.cashier_table.clear_table()
    return redirect(url_for('transactions'))


# -------------------------------------------------- #


# Inventory Page
# Requires: Login, Manager/Admin permission #
@app.route('/inventory')
@login_required
def inventory():
    if is_manager(current_user) or is_stocker(current_user):
        items = db.session.query(Item).all()
        return render_template("inventory.html", items=items, inventoryTable=POS_logic.stocker_table)
    else:
        return redirect('/')


@app.route('/stockeradd', methods=["POST"])
def stockerAddRow():
    # get the information from the user
    inputDict = POS_display.get_stocker_row(request)
    # get the product name from the database
    productName = POS_database.getProductName(db, inputDict['product_id'])
    # add all of the information received to the local stocking table
    POS_logic.stocker_table.add_row(inputDict['product_id'], productName, inputDict['inventory_cost'])
    return redirect(url_for('inventory'))

@app.route('/stockerdelete', methods=["POST"])
def stockerDeleteRow():
    inputDict = POS_display.get_stocker_row(request)
    POS_logic.stocker_table.delete_row(int(inputDict["row_number"]))
    return redirect(url_for('inventory'))

@app.route('/inventorycommit', methods=["POST"])
def updateInventory():
    # send all information from the local stocking table to the database for storage
    POS_database.updateItemTable(db, POS_logic.stocker_table.rowsList)
    # clear the local stocking table out
    POS_logic.stocker_table.clear_table()
    return redirect(url_for('inventory'))

@app.route('/stockercancel', methods=["POST"])
def stockerCancel():
    POS_logic.stocker_table.clear_table()
    return redirect(url_for('inventory'))


# -------------------------------------------------- #


# Register Page
# Requires: Login, Manager/Admin permission #
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    global current_user

    form = RegisterForm()
    if is_manager(current_user):
        if form.validate_on_submit():
            user = User(
                name=form.username.data,
                password=form.password.data,
                permissions=form.permission.data
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            current_user = user
            return redirect('/')

        else:
            return render_template("register.html", form=form)
    else:
        return redirect('/')


# -------------------------------------------------- #

#############################
# Database Page Routes
#############################


# itemsDB
# Requires: Login, Manager/Admin/Stocker permission #
@app.route('/itemsDB', methods=['GET', 'POST'])
@login_required
def itemsDB():
    result = db.session.query(Item).all()
    return render_template("itemsDB.html", itemsDBTable=result)

@app.route('/itemdb-delete', methods=["POST"])
@login_required
def itemDBDeleteItem():
    # get the user input from the form submit
    inputDict = POS_display.get_item_row(request)

    # delete the item  
    POS_database.destroyItem(db, inputDict["item-id"])

    # reload the page
    return redirect(url_for('itemsDB'))

@app.route('/itemdb-add', methods=["POST"])
def itemDBUpdateItem():
    # get the user input from the form submit
    inputDict = POS_display.get_item_row(request)

    #  if the user did enter an id number, check if its valid and modify item if it is
    #TODO check if the entered id number is valid
    if (inputDict["item-id"]):
        POS_database.editItem(db, inputDict["item-id"], inputDict["product-id"], inputDict["inventory-cost"])

    # else if the user did not enter an id, add a new item
    else:
        POS_database.addItem(db, inputDict["product-id"], inputDict["inventory-cost"])

    # reload the page
    return redirect(url_for('itemsDB'))

# -------------------------------------------------- #


# productsDB
# Requires: Login, Manager/Admin/Stocker permission #
@app.route('/productsDB', methods=['GET', 'POST'])
@login_required
def productsDB():
    result = db.session.query(Product).all()
    return render_template("productsDB.html", productsDBTable=result)

@app.route('/productdb-delete', methods=["POST"])
@login_required
def productDBDeleteProduct():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/productdb-add', methods=["POST"])
def productDBUpdateProduct():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('userDB'))

# -------------------------------------------------- #


# transactionsDB
# Requires: Login, Manager/Admin/Cashier permission #
@app.route('/transactionsDB', methods=['GET', 'POST'])
@login_required
def transactionsDB():
    result = db.session.query(Transaction).all()
    return render_template("transactionsDB.html", transactionsDBTable=result)

@app.route('/transactiondb-delete', methods=["POST"])
@login_required
def transactionDBDeleteTransaction():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/transactiondb-add', methods=["POST"])
def transactionDBUpdateTransaction():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('userDB'))

# -------------------------------------------------- #


# itemssoldDB
# Requires: Login, Manager/Admin/Cashier permission #
@app.route('/itemssoldDB', methods=['GET', 'POST'])
@login_required
def itemssoldDB():
    result = db.session.query(ItemSold).all()
    return render_template("itemssoldDB.html", itemsSoldDBTable=result)

@app.route('/itemsolddb-delete', methods=["POST"])
@login_required
def itemsoldDBDeleteItemsold():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/itemsolddb-add', methods=["POST"])
def itemsoldDBUpdateItemsold():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('itemssoldDB'))

# -------------------------------------------------- #


# discountsDB
# Requires: Login, Manager/Admin permission #
@app.route('/discountsDB', methods=['GET', 'POST'])
@login_required
def discountsDB():
    result = db.session.query(Discount).all()
    return render_template("discountsDB.html", discountsDBTable=result)

@app.route('/discountdb-delete', methods=["POST"])
@login_required
def discountDBDeleteDiscount():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/discountdb-add', methods=["POST"])
def discountDBUpdateDiscount():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('userDB'))

# -------------------------------------------------- #


# supplierDB
# Requires: Login, Manager/Admin permission #
@app.route('/supplierDB', methods=['GET', 'POST'])
@login_required
def supplierDB():
    result = db.session.query(Supplier).all()
    return render_template("suppliersDB.html", suppliersDBTable=result)

@app.route('/supplierdb-delete', methods=["POST"])
@login_required
def supplierDBDeleteSupplier():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/supplierdb-add', methods=["POST"])
def supplierDBUpdateSupplier():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('userDB'))

# -------------------------------------------------- #


# userDB
# Requires: Login, Manager/Admin permission #
@app.route('/userDB', methods=['GET', 'POST'])
@login_required
def userDB():
    result = db.session.query(User).all()
    return render_template("userDB.html", usersDBTable=result)

@app.route('/userdb-delete', methods=["POST"])
@login_required
def userDBDeleteUser():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    # delete the user  
    POS_database.destroyUser(db, inputDict["user_id"])

    # reload the page
    return redirect(url_for('userDB'))

@app.route('/userdb-add', methods=["POST"])
def userDBUpdateUser():
    # get the user input from the form submit
    inputDict = POS_display.get_user_row(request)

    #  if the user did enter an id number, check if its valid and modify user if it is
    #TODO check if the entered id number is valid
    if (inputDict["user_id"]):
        POS_database.editUser(db, inputDict["user_id"], inputDict["username"], inputDict["password"], inputDict["permissions"])

    # else if the user did not enter an id, add a new user
    else:
        POS_database.addUser(db, inputDict["username"], inputDict["password"], inputDict["permissions"])

    

    # reload the page
    return redirect(url_for('userDB'))


# -------------------------------------------------- #


# Used for local debugging
# Turn debug=False on to run without getting errors back when running locally
# Turn debug=True on to run locally and get error reports in the browser
if __name__ == '__main__':
    app.run(debug=True)
