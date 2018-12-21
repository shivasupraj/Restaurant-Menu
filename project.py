from flask import Flask, render_template, request ,redirect, url_for, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
 
from database_setup import Restaurant, Base, MenuItem
 
engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
#DBSession = sessionmaker(bind=engine)

session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

@app.route('/')
@app.route('/restaurants')
def restaurants():
    return 'All the available restaurants'

@app.route('/restaurants/new')
def newRestaurant():
    return 'Page fot new restaurant page'

@app.route('/restaurants/<int:restaurant_id>/edit')
def editRestaurant(restaurant_id):
    return 'Page to edit restaurant'

@app.route('/restaurants/<int:restaurant_id>/delete')
def deleteRestaurant(restaurant_id):
    return "Page to delete restaurant"

@app.route('/restaurants/<int:restaurant_id>/menu')
def restaurantMenu(restaurant_id):
    return 'Page to restaurant menu'

@app.route('/restaurants/<int:restaurant_id>/menu/new')
def addMenuItem(restaurant_id):
    return 'page to adding item to menu'

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit')
def editMenuItem(restaurant_id, menu_id):
    return "page to edit menu item"

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete')
def deleteMenuItem(restaurant_id, menu_id):
    return 'Page to delete menu item'


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)