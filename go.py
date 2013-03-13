import tornado.ioloop
import tornado.web
import tornado.database

import sqlite3
import sys
import datetime
import requests
import uuid

def build_db(db_file, cursor):
        f = open(db_file, 'r')
        with f:
            data = f.read()
        try:
            cursor.executescript(data)
        except sqlite3.Error as ex:
            print("Error (build_db): %s" % ex.args[0])
            sys.exit(1)

def _execute(query):
    dbPath = 'py_redirect.db'
    connection = sqlite3.connect(dbPath)
    cursorobj = connection.cursor()
    result = []
    try:
        cursorobj.execute(query)
        result = cursorobj.fetchall()
        connection.commit()
    except sqlite3.Error as ex:
        if 'no such table' in ex.args[0]:
            build_db('schema.sql', cursorobj)
            return
        print("Error (_execute()) %s:" % ex.args[0])
    connection.close()
    return result

def _gen_rand_url(url):
    temp = zlib.adler32(url.encode('utf-8'))

    return new_url
def track_event(cat, action, label):
    end_point = 'http://www.google-analytics.com/collect'
    ga_account = 'UA-35956241-1' # your analytics UA
    cid = str(uuid.uuid4())
    params = {'v' : 1,
            'tid' : ga_account,
            'cid' : cid,
            't' : 'event',
            'ec' : cat,
            'ea' : action,
            'el' : label}
    requests.post(end_point, data=params)

class MainHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.database = _execute('''SELECT shortlink,destination FROM redirects''')
        if not self.database:
            self.database = None
        else:
            self.database = dict(self.database)

    def get(self, shortlink=None):
        record = None
        if shortlink in self.database:
            record = self.database[shortlink]
        if record:
            if "http" not in record:
                record = "http://" + record
            self.redirect(record, True)
            track_event('Shortlink', 'Visit', shortlink + ': ' + record)
            return
        else:
            self.write("No such shortlink present.")
            track_event('Shortlink', 'Error', shortlink)


class CreateEntry(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/add.html')
 
    def post(self):
        shortlink = self.get_argument("shortlink")
        destination = self.get_argument("destination")
        query = ''' SELECT shortlink, destination FROM redirects WHERE shortlink = '%s' OR destination = '%s' ''' % (shortlink, destination)
        results = _execute(query)
        if not len(results):
            query = ''' insert into redirects (timestamp, shortlink, destination) values (%s, '%s', '%s') ''' %(datetime.date.today().isoformat(), shortlink, destination)
            _execute(query)
            self.render('templates/success.html')
        else:
            results = dict(results)
            if shortlink in results:
                self.write("Shortlink %s already exists and points to %s" % (shortlink, results[shortlink]))
            else:
                self.write("Destination URL %s already has a shortlink, %s" % (destination, [x for x in results.keys()][0]))
        

class ShowEntries(tornado.web.RequestHandler):
    def get(self):
        query = ''' select * from redirects'''
        rows = _execute(query)
        self._processresponse(rows)
 
    def _processresponse(self,rows):
        self.write("<b>Records</b> <br /><br />")
        for row in rows:
                self.write(str(row[0]) + "      " + str(row[2]) + "     " + str(row[3]) +" <br />" )

application = tornado.web.Application([
    (r"/_create|/$", CreateEntry),
    (r"/_show", ShowEntries),
    (r"/(.*)", MainHandler),   
])

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()