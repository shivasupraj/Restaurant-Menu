from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Restaurant, Base, MenuItem
 
engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:                        
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<a href='restaurants/new'><h3>New Restaurant</h3></a>"
                restaurants = session.query(Restaurant).all()
                for restaurant in restaurants:
                    output += "<p>" + restaurant.name + "</br>"
                    output += "<a href=%s>Edit</a></br>" % ('/restaurents/' + str(restaurant.id) + '/edit')
                    output += "<a href='/restaurants/%s/delete'>Delete</a></br></p>" % restaurant.id
                output += "</body></html>"
                self.wfile.write(output)
                #print(output)
                return

            elif self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Make a new restaurant</h1>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><input name="message" type="text" ><input type="submit" value="Submit"> </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                print(output)
                return
            elif self.path.endswith("/edit"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                id = self.path.split('/')[2]
                restaurant = session.query(Restaurant).filter_by(id = id)[0]
                output = ""
                output += "<html><body>"
                output += "<h1>Edit the restaurant %s</h1>" % restaurant.name
                output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'><input name="message" type="text" ><input type="submit" value="Submit"> </form>''' % id
                output += "</body></html>"
                self.wfile.write(output)
            elif self.path.endswith("/delete"):
                self.send_response(200)
                self.send_header('Content-type', 'text-html')
                self.end_headers()
                id = self.path.split('/')[2]
                restaurant = session.query(Restaurant).filter_by(id = id).first()
                output = ""
                output += "<html><body>"
                output += "<h1>Do you want to delete %s <h1>" % restaurant.name
                output += '''<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/delete'><input type="submit" value="Delete"> </form>''' % id
                output += "</body></html>"
                self.wfile.write(output)
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/restaurants/new"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location','/restaurants')
                self.end_headers()
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('message')
                restaurant = Restaurant(name = messagecontent[0])
                session.add(restaurant)
                session.commit()
            elif self.path.endswith("/edit"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location','/restaurants')
                self.end_headers()
                id = self.path.split('/')[2]
                restaurant = session.query(Restaurant).filter_by(id = id).first()
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('message')
                restaurant.name = messagecontent[0]
                session.add(restaurant)
                session.commit()
            elif self.path.endswith("/delete"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()
                id = self.path.split('/')[2]
                restaurant = session.query(Restaurant).filter_by(id = id).first()
                session.delete(restaurant)
                session.commit()
        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print("Web Server running on port %s" % port)
        server.serve_forever()
    except KeyboardInterrupt:
        print(" ^C entered, stopping web server....")
        server.socket.close()

if __name__ == '__main__':
    main()