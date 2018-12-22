from flask import Flask, render_template, request ,redirect, url_for, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
 
from database_setup import Restaurant, Base, MenuItem
 
engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 


#Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree', 'id' : '1'}


#DBSession = sessionmaker(bind=engine)

session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

@app.route('/')
@app.route('/restaurants')
def restaurantsList():
    restaurants = session.query(Restaurant).all()
    if len(restaurants) == 0:
        flash('Could n\'t load any restaurants')
    return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurants/new', methods = ['GET', 'POST'])
def newRestaurant():
    if request.method == 'GET':
        return render_template('newRestaurant.html')
    else:
        form = request.form
        if 'restaurant_name' in form:
            restaurant_name = form['restaurant_name']
        else:
            flash('Could n\'t add the new restaurant ')
            return redirect(url_for('restaurantsList'))
        restaurant = Restaurant(name = restaurant_name)
        session.add(restaurant)
        session.commit()
        flash('Added the new restaurant succesfully')
        return redirect(url_for('restaurantsList'))


@app.route('/restaurants/<int:restaurant_id>/edit', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
    if request.method == 'GET':
        print(request.form)
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            return redirect(url_for('restaurantsList'))
        restaurant = sqlalchemy_obj.one()
        return render_template('editRestaurant.html', restaurant = restaurant)
    else:
        form = request.form
        if len(form) > 0 and 'restaurant_name' in form:
            restaurant_name = form['restaurant_name']
        else:
            flash('Could not update to the database')
            return redirect(url_for('restaurantsList'))
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not update to the database')
            return redirect(url_for('restaurantsList'))
        else:
            restaurant = sqlalchemy_obj.one()
            restaurant.name = restaurant_name
            session.add(restaurant)
            session.commit()
            flash('Updated the entry successfully')
            return redirect(url_for('restaurantsList'))




@app.route('/restaurants/<int:restaurant_id>/delete', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if request.method == 'GET':
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not delete the restaurant')
            return redirect(url_for('restaurantsList'))
        else:
            restaurant = sqlalchemy_obj.one()
            return render_template('deleteRestaurant.html', restaurant = restaurant)
    else:
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not delete the restaurant')
        else:
            restaurant = sqlalchemy_obj.one()
            session.delete(restaurant)
            session.commit()
            flash('Deleted the restaurant succesfully')
        return redirect(url_for('restaurantsList'))



@app.route('/restaurants/<int:restaurant_id>/menu')
def restaurantMenu(restaurant_id):
    return render_template('menu.html', items = items, restaurant = restaurant)

@app.route('/restaurants/<int:restaurant_id>/menu/new')
def addMenuItem(restaurant_id):
    return render_template('newMenuItem.html', restaurant = restaurant)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit')
def editMenuItem(restaurant_id, menu_id):
    return render_template('editMenuItem.html', restaurant = restaurant, item = item)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete')
def deleteMenuItem(restaurant_id, menu_id):
    return render_template('deleteMenuItem.html', item = item, restaurant = restaurant)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)