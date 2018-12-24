from flask import Flask, render_template, request ,redirect, url_for, flash, jsonify
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
from flask import make_response
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from database_setup import Restaurant, Base, MenuItem

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 


#Fake Restaurants
#restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

#restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
#items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
#item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree', 'id' : '1'}


#DBSession = sessionmaker(bind=engine)

session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the autharization code .'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token Info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
    # Verify that the access token is used for the intended user
    gplus_id =  credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token\'s user id don\'t match given user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/restaurants')
def restaurantsList():
    restaurants = session.query(Restaurant).all()
    if len(restaurants) == 0:
        flash('Could n\'t load any restaurants')
    return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurants/new', methods = ['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')

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
    if 'username' not in login_session:
        return redirect('/login')
        
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
    if 'username' not in login_session:
        return redirect('/login')
        
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
    if 'username' not in login_session:
        return redirect('/login')
        
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
    if 'username' not in login_session:
        return redirect('/login')
        
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
    if 'username' not in login_session:
        return redirect('/login')
        
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

#API end points

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    MenuItems = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in MenuItems])

@app.route('/restaurants/JSON')
def restaurantsListJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[i.serialize for i in restaurants])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def restaurantMenuItem(restaurant_id, menu_id):
    sqlalchemy_obj = session.query(Restaurant).filter_by(id = restaurant_id)
    if sqlalchemy_obj.count() == 0:
        return jsonify(restaurants=[])
    sqlalchemy_obj = session.query(MenuItem).filter_by(id = menu_id)
    if sqlalchemy_obj.count() == 0:
        return jsonify(restaurants=[])
    items = sqlalchemy_obj
    return jsonify(MenuItem=[i.serialize for i in items])



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)