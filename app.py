# Imports
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random, string, httplib2, json, requests

app = Flask(__name__)

# Google client id
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# connect to the data base
engine = create_engine('sqlite:///itemCatalogWithUsers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# login page
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html',STATE = state)

	
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    
    stored_credntials = login_session.get('credntials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credntials is not None and gplus_id == stored_gplus_id:
        login_session['credentials'] = credentials.access_token
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

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
   
    # see if user exist,if not make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
	user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

	
# User Helper Functions 1/3
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

	
# User Helper Functions 2/3
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

	
# User Helper Functions 3/3	
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

		
# GDisconnect the current user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
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

		
# Display the main page that has all the categories
@app.route('/')
@app.route('/catalog')
def showCatalog():
	categories = session.query(Categories).all()
	if 'username' not in login_session:
		return render_template('publicCategories.html', categories = categories)
	else:
		return render_template('catalog.html',categories = categories)

		
# creates new category
@app.route('/category/new', methods = ['GET','POST'])
def newCategory():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST': 
		if request.form['name']:
			newcategory = Categories(name = request.form['name'], user_id = login_session['user_id'])
		session.add(newcategory)
		session.commit()
		flash('"'+newcategory.name+'" has been added to the menu.')
		return redirect(url_for('showCatalog'))
	else:
		return render_template('newCategories.html')	

		
# "This function will be for editing category/ %s"  %categories_id
@app.route('/catalog/<int:categories_id>/edit' , methods = ['GET','POST'])
def editCategory(categories_id):
	if 'username' not in login_session:
		return redirect('/login')
	edited_category = session.query(Categories).filter_by(id=categories_id).one()
	if edited_category.user_id != login_session['user_id']:
		flash('You are not authorized to edit this category. Please create your own category in order to edit.')
		return redirect(url_for('showCatalog'))       
	if request.method == 'POST':
		if request.form['name']:
			edited_category.name = request.form['name']
		session.add(edited_category)
		session.commit()
		flash("'"+edited_category.name+"' has been edited successfully.")
		return redirect(url_for('showCatalog'))
	else:
		return render_template('editCategory.html', edited_category = edited_category)		

		
# "This function will be for deleting category %s"  %categories_id
@app.route('/catalog/<int:categories_id>/delete', methods = ['GET','POST'])
def deleteCategory(categories_id):
	if 'username' not in login_session:
		return redirect('/login')
	deleted_category = session.query(Categories).filter_by(id=categories_id).one()	
	if deleted_category.user_id != login_session['user_id']:
		flash('You are not authorized to delete this category. Please create your own category in order to delete.')
		return redirect(url_for('showCatalog'))
	if request.method == 'POST':
		session.delete(deleted_category)
		session.commit()
		flash("'"+deleted_category.name+"' has been successfully deleted.")
		return redirect(url_for('showCatalog'))
	else:
		return render_template('deleteCategory.html', deleted_category = deleted_category)  

		
# "This page will show the items of a category %s"  %categories_id
@app.route('/catalog/<int:categories_id>/items')
def showItems(categories_id):
	category = session.query(Categories).filter_by(id=categories_id).one()
	creator = getUserInfo(category.user_id)
	items = session.query(Items).filter_by(categories_id = categories_id)
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicCategoryItems.html', category = category, items = items, creator = creator)
	else:
		return render_template('items.html',category = category, items = items)

        
# "This function will make a new item in a category %s"  %categories_id
@app.route('/catalog/<int:categories_id>/item/new', methods =['GET','POST'])
def newCategoryItem(categories_id):
	if 'username' not in login_session:
		return redirect('/login')
	category = session.query(Categories).filter_by(id=categories_id).one()
	if login_session['user_id'] != category.user_id:
		return "<script>function myFunction() {alert('You are not authorized to add new items to this category. Please create your own category in order to add items.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		if request.form['name']:
			new_item = Items(name = request.form['name'], description = request.form['description'], price = request.form['price'], categories_id = categories_id)
		session.add(new_item)
		session.commit()
		flash ("'"+request.form['name']+"' has been add to your category.")
		return redirect(url_for('showItems', categories_id = category.id))
	else:
		return render_template('newCategoryItem.html', category = category)

		
# "This function will edit the category item %s"  %items_id
@app.route('/catalog/<int:categories_id>/Item/<int:items_id>/edit' , methods = ['GET','POST'])
def editCategoryItem(categories_id,items_id):
	if 'username' not in login_session:
		return redirect('/login')
	edited_item = session.query(Items).filter_by(id = items_id).one()
	category = session.query(Categories).filter_by(id = categories_id).one()
	if login_session['user_id'] != restaurant.user_id:
		return "<script>function myFunction() {alert('You are not authorized to edit items to this category. Please create your own category in order to edit items.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		if request.form['name']:
			edited_item.name = request.form['name']
		if request.form['description']:
				edited_item.description = request.form['description']
		if request.form['price']:
			edited_item.price = request.form['price']
		session.add(edited_item)
		session.commit()
		flash("'"+edited_item.name+"' has been modified.")
		return redirect(url_for('showItems', categories_id = category.id))
	else: 
		return render_template('editCategoryItem.html', item = edited_item, category = category)

		
# "This function will delete the category item %s"  %items_id
@app.route('/catalog/<int:categories_id>/item/<int:items_id>/delete' , methods = ['get','post'])
def deleteCategoryItem(categories_id,items_id):
	if 'username' not in login_session:
		return redirect('/login')
	deleted_item = session.query(Items).filter_by(id =items_id).one()
	category = session.query(Categories).filter_by(id = categories_id).one()
	if login_session['user_id'] != restaurant.user_id:
		return "<script>function myFunction() {alert('You are not authorized to delete items to this category. Please create your own category in order to delete items.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		session.delete(deleted_item)
		session.commit()
		flash("'"+deleted_item.name+"' has been deleted successfully.")
		return redirect(url_for('showItems', categories_id = category.id))
	else:
		return render_template('deleteCategoryItem.html', item = deleted_item, category = category)

		
# JSON APIs to view all the categories.
@app.route('/catalog/JSON')
def showCatalogJSON():
	categories = session.query(Categories).all()
	return jsonify(Categories = [i.serialize for i in categories])

	
# JSON APIs to view Category Information.
@app.route('/catalog/<int:categories_id>/items/JSON')
def showCategoryItemsJSON(categories_id):
	categories = session.query(Categories).filter_by(id= categories_id).one()
	items = session.query(Items).filter_by(categories_id = categories_id).all()
	return jsonify(Items = [i.serialize for i in items])

	
# JSON APIs to view item in specific category.
@app.route('/catalog/<int:categories_id>/item/<int:items_id>/JSON')
def showItemJSON(categories_id, items_id):
   	 item = session.query(Items).filter_by(id=items_id).one()
    	 return jsonify(Items = item.serialize)

		 
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
