from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantMenu.db')
Base.metadata.bind=engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            
            if self.path.endswith("/delete"):
                restaurantid = self.path.split("/")[2]
                myupdatequery = session.query(Restaurant).filter_by(id=restaurantid).one()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
		output += "<h1>Are you sure you want to Delete %s</h1>" % myupdatequery.name
                output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/delete'>"  % restaurantid
                output += "<input type='submit' value='Delete'>"
                output += "</form>"
                output += "</body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith("/edit"):
                restaurantIDPath = self.path.split("/")[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(
                    id=restaurantIDPath).one()
                if myRestaurantQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<html><body>"
                    output += "<h1>"
                    output += myRestaurantQuery.name
                    output += "</h1>"
                    output += "<form method='POST' enctype='multipart/form-data' action = '/restaurants/%s/edit' >" % restaurantIDPath
                    output += "<input name = 'newRestaurantName' type='text' placeholder = '%s' >" % myRestaurantQuery.name
                    output += "<input type = 'submit' value = 'Rename'>"
                    output += "</form>"
                    output += "</body></html>"
                    self.wfile.write(output)

            if self.path.endswith("/restaurants/new"):
            	results = session.query(Restaurant).all()
            	self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
            	output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><h2>Make a new Restaurant</h2><input name="message" type="text" ><input type="submit" value="Create"> </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return

           
            if self.path.endswith("/restaurants"):
            	results = session.query(Restaurant).all()
            	self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants'><h2>Make a new Restaurant</h2><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                for restaurant in results:
                	output+=restaurant.name
                        output+="</br>"
                        output+="<a href='/restaurants/%s/edit'>Edit</a>" % restaurant.id
               	        output+="</br>"
               	        output+="<a href='/restaurants/%s/delete'>Delete</a>" %restaurant.id
                        output+="</br></br></br>" 
                output += "</body></html>"
                self.wfile.write(output)
                print output
                return


        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
          
            if self.path.endswith("/delete"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                restaurantid = self.path.split("/")[2]
                myupdatequery = session.query(Restaurant).filter_by(id=restaurantid).one()
                if myupdatequery != []:
		    session.delete(myupdatequery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()
                    self.wfile.write(output)

	    if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')
                    restaurantIDPath = self.path.split("/")[2]

                    myRestaurantQuery = session.query(Restaurant).filter_by(
                        id=restaurantIDPath).one()
                    if myRestaurantQuery != []:
                        myRestaurantQuery.name = messagecontent[0]
                        session.add(myRestaurantQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/restaurants')
                        self.end_headers()
      
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                messagecontent = fields.get('message')
            	newrestaurant = Restaurant(name = messagecontent[0])
		session.add(newrestaurant)
		sesssion.commit()
	    output = ""
            output += "<html><body>"
            output += " <h2> Okay, how about this: </h2>"
            output += "<h1> %s </h1>" % messagecontent[0]
            output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants'><h2>Make a new Restaurant</h2><input name="message" type="text" ><input type="submit" value="submit"> </form>'''
            output += "</body></html>"
            self.wfile.write(output)
            print output
             

        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()