#!/usr/bin/python3

"""
AUTHOR: Matthew May - mcmay.web@gmail.com
"""

# Imports
import json
# import redis
import tornadoredis
# import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import re
# from os import getuid, path
import os.path
from sys import exit
from mapconst import SERVICE_RGB, REDIS_IP, WEBSOCK_PORT, BLOCK_IP_LIST_FILE


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(request):
        service_items = list()
        for name, rgb in SERVICE_RGB.items():
            service_items.append({"name":name, "rgb":rgb})
        request.render('index.html', service_items=service_items)


class WebSocketChatHandler(tornado.websocket.WebSocketHandler):
    
    def __init__(self, *args, **kwargs):
        super(WebSocketChatHandler, self).__init__(*args, **kwargs)
        self.listen()
    
    def check_origin(self, origin):
        return True
    
    @tornado.gen.engine
    def listen(self):
        
        print('[*] WebSocketChatHandler opened')
        
        try:
            # This is the IP address of the DataServer
            self.client = tornadoredis.Client(REDIS_IP)
            self.client.connect()
            print('[*] Connected to Redis server')
            yield tornado.gen.Task(self.client.subscribe, 'attack-map-production')
            self.client.listen(self.on_message)
        except Exception as ex:
            print('[*] Could not connect to Redis server.')
            print('[*] {}'.format(str(ex)))
    
    def on_close(self):
        print('[*] Closing connection.')
    
    # This function is called everytime a Redis message is received
    def on_message(self, msg):
        
        if len(msg) == 0:
            print("msg == 0\n")
            return None
        
        if 'ip_blocked' in msg:
            ip = re.split(":", msg)
            with open(BLOCK_IP_LIST_FILE, 'a') as f:
                f.write(ip[1] + "\n")
        
        try:
            json_data = json.loads(msg.body)
        except Exception as ex:
            return None
        
        json_data.update({
            'color':SERVICE_RGB.get(
                    json_data.get('protocol'),
                    SERVICE_RGB.get("OTHER"))})
        
        self.write_message(json.dumps(json_data))


def main():
    # Register handler pages
    handlers = [
        (r'/', IndexHandler),
        (r'/websocket', WebSocketChatHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path':'static'}),
        (r'/flags/(.*)', tornado.web.StaticFileHandler, {'path':'static/flags'}),
    ]
    
    # Define static settings
    settings = {
        # Define the static path
        # static_path = path.join( path.dirname(__file__), 'static' )
        # 'static_path': static_path
        "template_path":os.path.join(os.path.dirname(__file__), 'templates'),
    }
    
    # Create and start app listening on port 8888
    try:
        app = tornado.web.Application(handlers, **settings)
        app.listen(WEBSOCK_PORT)
        print('[*] Waiting on browser connections...')
        tornado.ioloop.IOLoop.instance().start()
    except Exception as appFail:
        print(appFail)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nSHUTTING DOWN')
        exit()
