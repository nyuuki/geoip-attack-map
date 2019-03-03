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
# import re

# from os import getuid, path
# from os import path
from sys import exit

# Look up service colors
service_rgb = {
    'FTP':'#ff0000',
    'SSH':'#ff8000',
    'TELNET':'#ffff00',
    'EMAIL':'#80ff00',
    'WHOIS':'#00ff00',
    'DNS':'#00ff80',
    'HTTP':'#00ffff',
    'HTTPS':'#0080ff',
    'SQL':'#0000ff',
    'SNMP':'#8000ff',
    'SMB':'#bf00ff',
    'AUTH':'#ff00ff',
    'RDP':'#ff0060',
    'DoS':'#ff0000',
    'ICMP':'#ffcccc',
    'OTHER':'#6600cc'
}


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(request):
        request.render('index.html')


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
            self.client = tornadoredis.Client('127.0.0.1')
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
        
        # if 'ip_blocked' in msg:
        #    ip = re.split(":", msg)
        # fp = open('/mnt/map_attack_blk/LOG4.log','a')
        # fp.write(ip[1]+"\n")
        # fp.close()
        
        try:
            json_data = json.loads(msg.body)
        except Exception as ex:
            return None
        
        msg_type = json_data.get('msg_type')
        msg_type2 = json_data.get('msg_type2')
        msg_type3 = json_data.get('msg_type3')
        protocol = json_data.get('protocol')
        color = service_rgb.get(protocol, '#000000')
        src_ip = json_data.get('src_ip')
        dst_ip = json_data.get('dst_ip')
        src_port = json_data.get('src_port')
        dst_port = json_data.get('dst_port')
        src_lat = json_data.get('latitude')
        src_long = json_data.get('longitude')
        dst_lat = json_data.get('dst_lat')
        dst_long = json_data.get('dst_long')
        city = json_data.get('city')
        continent = json_data.get('continent')
        continent_code = json_data.get('continent_code')
        country = json_data.get('country')
        iso_code = json_data.get('iso_code')
        postal_code = json_data.get('postal_code')
        event_count = json_data.get('event_count')
        continents_tracked = json_data.get('continents_tracked')
        countries_tracked = json_data.get('countries_tracked')
        ips_tracked = json_data.get('ips_tracked')
        unknowns = json_data.get('unknowns')
        event_time = json_data.get('event_time')
        country_to_code = json_data.get('country_to_code')
        ip_to_code = json_data.get('ip_to_code')
        
        msg_to_send = {
            'type':msg_type,
            'type2':msg_type2,
            'type3':msg_type3,
            'protocol':protocol,
            'src_ip':src_ip,
            'dst_ip':dst_ip,
            'src_port':src_port,
            'dst_port':dst_port,
            'src_lat':src_lat,
            'src_long':src_long,
            'dst_lat':dst_lat,
            'dst_long':dst_long,
            'city':city,
            'continent':continent,
            'continent_code':continent_code,
            'country':country,
            'iso_code':iso_code,
            'postal_code':postal_code,
            'color':color,
            'event_count':event_count,
            'continents_tracked':continents_tracked,
            'countries_tracked':countries_tracked,
            # 'ips_tracked': "<a href='" + str(ips_tracked) + "'>" + str(ips_tracked) + "</a>",
            'ips_tracked':ips_tracked,
            'unknowns':unknowns,
            'event_time':event_time,
            'country_to_code':country_to_code,
            'ip_to_code':ip_to_code,
        }
        
        self.write_message(json.dumps(msg_to_send))


def main():
    # Register handler pages
    handlers = [
        (r'/websocket', WebSocketChatHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path':'static'}),
        (r'/flags/(.*)', tornado.web.StaticFileHandler, {'path':'static/flags'}),
        (r'/', IndexHandler)
    ]
    
    # Define the static path
    # static_path = path.join( path.dirname(__file__), 'static' )
    
    # Define static settings
    settings = {
        # 'static_path': static_path
    }
    
    # Create and start app listening on port 8888
    try:
        app = tornado.web.Application(handlers, **settings)
        app.listen(8889)
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
