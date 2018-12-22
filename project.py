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
    sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
    if sqlalchemy_obj.count() == 0:
        flash('No menu available for this restaurant')
        return redirect(url_for('restaurantsList'))
    restaurant = sqlalchemy_obj.one()
    sqlalchemy_obj = session.query(MenuItem).filter_by(restaurant = restaurant)
    if sqlalchemy_obj.count() == 0:
        flash('No menu available for this restaurant')
        return redirect(url_for('restaurantsList'))
    items = sqlalchemy_obj
    return render_template('menu.html', items = items, restaurant = restaurant)

@app.route('/restaurants/<int:restaurant_id>/menu/new', methods = ['GET', 'POST'])
def addMenuItem(restaurant_id):
    if request.method == 'GET':
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('No menu available for this restaurant')
            return redirect(url_for('restaurantsList'))
        restaurant = sqlalchemy_obj.one()
        return render_template('newMenuItem.html', restaurant = restaurant)
    else:
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('No menu available for this restaurant')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        else:
            restaurant = sqlalchemy_obj.one()
        form = request.form
        if len(form) > 0 and 'menu_name' in form:
            menu_name = form['menu_name']
        else:
            flash('Cannot add the menu item to menu')
            return redirect(url_for('restaurantsList'))
        description = form['description'] if 'description' in form else None
        price =  '$' + str(form['price']) if 'price' in form else None
        course = form['course'] if 'course' in form else None
        menu_item = MenuItem(name = menu_name, description = description, price = price, course = course, restaurant = restaurant)
        session.add(menu_item)
        session.commit()
        flash('Added the menu item to the menu')
        return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if request.method == 'GET':
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not find the restaurant')
            return redirect(url_for('retaurantsList'))
        restaurant = sqlalchemy_obj.one()
        sqlalchemy_obj = session.query(MenuItem).filter_by(id = menu_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not find the menu')
            return redirect(url_for('restaurantsList'))
        item = sqlalchemy_obj.one()
        return render_template('editMenuItem.html', restaurant = restaurant, item = item)
    else:
        sqlalchemy_obj = session.query(MenuItem).filter_by(id = menu_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not update the menu item to the menu')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        menu = sqlalchemy_obj.one()
        form = request.form
        if len(form) == 0:
            flash('Could not update the menu item to the menu')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        print(menu.name)
        if 'menu_name' in form:
            menu.name = form['menu_name'] 
        if 'description' in form:
            menu.description = form['description'] 
        if 'price' in form:
            menu.price =  '$' + str(form['price']) 
        if 'course' in form:
            menu.course = form['course'] 
        session.add(menu)
        session.commit()
        flash('updated the menu item to the menu')
        return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if request.method == 'GET':
        sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not load the restaurant')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        restaurant = sqlalchemy_obj.one()
        sqlalchemy_obj = session.query(MenuItem).filter_by(id = menu_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not load the menu item')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        item = sqlalchemy_obj.one()
        return render_template('deleteMenuItem.html', item = item, restaurant = restaurant)
    else:
        sqlalchemy_obj = session.query(MenuItem).filter_by(id = menu_id)
        if sqlalchemy_obj.count() == 0:
            flash('Could not delete the menu item')
            return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
        item = sqlalchemy_obj.one()
        session.delete(item)
        session.commit()
        flash('Deleted the menu item successfully')
        return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)