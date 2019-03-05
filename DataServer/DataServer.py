#!/usr/bin/python3

"""
AUTHOR: Matthew May - mcmay.web@gmail.com
"""

# Imports
import json
import redis
import io
from sys import exit
from const import META, PORTMAP, REDIS_IP, SYSLOG_PATH, DB_PATH, HQ_IP
from time import gmtime, localtime, sleep, strftime
import maxminddb

# import logging
# import re
# from argparse import ArgumentParser, RawDescriptionHelpFormatter
# from os import getuid
# from textwrap import dedent

# Create clean dictionary using unclean db dictionary contents
server_start_time = strftime("%d-%m-%Y %H:%M:%S", localtime())  # local time
event_count = 0
continents_tracked = {}
countries_tracked = {}
country_to_code = {}
ip_to_code = {}
ips_tracked = {}
unknowns = {}


# @IDEA
# ---------------------------------------------------------
# Use a class to nicely wrap everything:
# Could attempt to do an access here
# now without worrying about key errors,
# or just keep the filled data structure
#
# class Instance(dict):
#
#    defaults = {
#                'city': {'names':{'en':None}},
#                'continent': {'names':{'en':None}},
#                'continent': {'code':None},
#                'country': {'names':{'en':None}},
#                'country': {'iso_code':None},
#                'location': {'latitude':None},
#                'location': {'longitude':None},
#                'location': {'metro_code':None},
#                'postal': {'code':None}
#                }
#
#    def __init__(self, seed):
#        self(seed)
#        backfill()
#
#    def backfill(self):
#        for default in self.defaults:
#            if default not in self:
#                self[default] = defaults[default]
# ---------------------------------------------------------

# def menu():
# Instantiate parser
# parser = ArgumentParser(
#        prog='DataServer.py',
#        usage='%(progs)s [OPTIONS]',
#        formatter_class=RawDescriptionHelpFormatter,
#        description=dedent('''\
#                --------------------------------------------------------------
#                Data server for attack map application.
#                --------------------------------------------------------------'''))

# @TODO --> Add support for command line args?
# define command line arguments
# parser.add_argument('-db', '--database', dest='DB_PATH', required=True, type=str, help='path to maxmind database')
# parser.add_argument('-m', '--readme', dest='readme', help='print readme')
# parser.add_argument('-o', '--output', dest='output', help='file to write logs to')
# parser.add_argument('-r', '--random', action='store_true', dest='randomize', help='generate random IPs/protocols for demo')
# parser.add_argument('-rs', '--redis-server-ip', dest='REDIS_IP', type=str, help='redis server ip address')
# parser.add_argument('-sp', '--syslog-path', dest='SYSLOG_PATH', type=str, help='path to syslog file')
# parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='run server in verbose mode')

# Parse arguments/options
# args = parser.parse_args()
# return args


def clean_db(unclean):
    selected = {}
    for tag in META:
        if tag['tag'] in unclean:
            head = unclean[tag['tag']]
            for node in tag['path']:
                if node in head:
                    head = head[node]
                else:
                    head = None
                    break
            selected[tag['lookup']] = head
    
    return selected


def connect_redis():
    r = redis.StrictRedis(host=REDIS_IP, port=6379, db=0)
    return r


def get_msg_type():
    # @TODO
    # Add support for more message types later
    return "Traffic"


# Check to see if packet is using an interesting TCP/UDP protocol based on source or destination port
def get_tcp_udp_proto(src_port, dst_port):
    src_port = int(src_port)
    dst_port = int(dst_port)
    
    if src_port in PORTMAP:
        return PORTMAP[src_port]
    if dst_port in PORTMAP:
        return PORTMAP[dst_port]
    
    return "OTHER"


def find_hq_lat_long():
    hq_ip_db_unclean = parse_maxminddb(HQ_IP)
    if hq_ip_db_unclean:
        hq_ip_db_clean = clean_db(hq_ip_db_unclean)
        dst_lat = hq_ip_db_clean['latitude']
        dst_long = hq_ip_db_clean['longitude']
        hq_dict = {
            'dst_lat':dst_lat,
            'dst_long':dst_long
        }
        return hq_dict
    else:
        print('Please provide a valid IP address for headquarters')
        exit()


def parse_maxminddb(ip):
    try:
        reader = maxminddb.open_database(DB_PATH)
        response = reader.get(ip)
        reader.close()
        return response
    except FileNotFoundError:
        print('DB not found')
        print('SHUTTING DOWN')
        exit()
    except ValueError:
        return False


# @TODO
# Refactor/improve parsing
# This function depends heavily on which appliances are generating logs
# For now it is only here for testing

def parse_syslog(line):
    line = line.split()
    data = line[-1]
    data = data.split(',')
    
    if len(data) != 6:
        print('NOT A VALID LOG')
        return False
    else:
        src_ip = data[0]
        dst_ip = data[1]
        src_port = data[2]
        dst_port = data[3]
        type_attack = data[4]
        cve_attack = data[5]
        data_dict = {
            'src_ip':src_ip,
            'dst_ip':dst_ip,
            'src_port':src_port,
            'dst_port':dst_port,
            'type_attack':type_attack,
            'cve_attack':cve_attack
        }
        return data_dict


def shutdown_and_report_stats():
    print('\nSHUTTING DOWN')
    # Report stats tracked
    print('\nREPORTING STATS...')
    print('\nEvent Count: {}'.format(event_count))  # report event count
    print('\nContinent Stats...')  # report continents stats
    for key in continents_tracked:
        print('{}: {}'.format(key, continents_tracked[key]))
    print('\nCountry Stats...')  # report country stats
    for country in countries_tracked:
        print('{}: {}'.format(country, countries_tracked[country]))
    print('\nCountries to iso_codes...')
    for key in country_to_code:
        print('{}: {}'.format(key, country_to_code[key]))
    print('\nIP Stats...')  # report IP stats
    for ip in ips_tracked:
        print('{}: {}'.format(ip, ips_tracked[ip]))
    print('\nIPs to iso_codes...')
    for key in ip_to_code:
        print('{}: {}'.format(key, ip_to_code[key]))
    print('\nUnknowns...')
    for key in unknowns:
        print('{}: {}'.format(key, unknowns[key]))
    exit()


def merge_dicts(*args):
    super_dict = {}
    for arg in args:
        super_dict.update(arg)
    return super_dict


def track_flags(super_dict, tracking_dict, key1, key2):
    if key1 in super_dict:
        if key2 in super_dict:
            if key1 in tracking_dict:
                tracking_dict[super_dict[key1]] = super_dict[key2]
    return


def track_stats(super_dict, tracking_dict, key):
    node = super_dict.get(key, False)
    if node is not False:
        if node in tracking_dict:
            tracking_dict[node] += 1
        else:
            tracking_dict[node] = 1
    else:
        if key in unknowns:
            unknowns[key] += 1
        else:
            unknowns[key] = 1


def main():
    # if getuid() != 0:
    #    print('Please run this script as root')
    #    print('SHUTTING DOWN')
    #    exit()
    
    global continents_tracked, countries_tracked, ips_tracked, \
        event_count, ip_to_code, country_to_code
    
    # args = menu()
    
    # Connect to Redis
    redis_instance = connect_redis()
    # Find HQ lat/long
    hq_dict = find_hq_lat_long()
    
    # Follow/parse/format/publish syslog data
    with io.open(SYSLOG_PATH, "r", encoding='ISO-8859-1') as syslog_file:
        syslog_file.readlines()
        
        while True:
            where = syslog_file.tell()
            line = syslog_file.readline()
            if not line:
                sleep(.1)
                syslog_file.seek(where)
            else:
                syslog_data_dict = parse_syslog(line)
                if syslog_data_dict:
                    ip_db_unclean = parse_maxminddb(syslog_data_dict['src_ip'])
                    if ip_db_unclean:
                        event_count += 1
                        ip_db_clean = clean_db(ip_db_unclean)
                        
                        msg_type = {'msg_type':get_msg_type()}
                        msg_type2 = {'msg_type2':syslog_data_dict['type_attack']}
                        msg_type3 = {'msg_type3':syslog_data_dict['cve_attack']}
                        
                        proto = {'protocol':get_tcp_udp_proto(
                                syslog_data_dict['src_port'],
                                syslog_data_dict['dst_port']
                        )}
                        super_dict = merge_dicts(
                                hq_dict,
                                ip_db_clean,
                                msg_type,
                                msg_type2,
                                msg_type3,
                                proto,
                                syslog_data_dict
                        )
                        
                        # Track Stats
                        track_stats(super_dict, continents_tracked, 'continent')
                        track_stats(super_dict, countries_tracked, 'country')
                        track_stats(super_dict, ips_tracked, 'src_ip')
                        event_time = strftime("%d-%m-%Y %H:%M:%S", localtime())  # local time
                        # event_time = strftime("%Y-%m-%d %H:%M:%S", gmtime()) # UTC time
                        track_flags(super_dict, country_to_code, 'country', 'iso_code')
                        track_flags(super_dict, ip_to_code, 'src_ip', 'iso_code')
                        
                        # Append stats to super_dict
                        super_dict['event_count'] = event_count
                        super_dict['continents_tracked'] = continents_tracked
                        super_dict['countries_tracked'] = countries_tracked
                        super_dict['ips_tracked'] = ips_tracked
                        super_dict['unknowns'] = unknowns
                        super_dict['event_time'] = event_time
                        super_dict['country_to_code'] = country_to_code
                        super_dict['ip_to_code'] = ip_to_code
                        
                        json_data = json.dumps(super_dict)
                        redis_instance.publish('attack-map-production', json_data)
                        
                        # if args.verbose:
                        #    print(ip_db_unclean)
                        #    print('------------------------')
                        #    print(json_data)
                        #    print('Event Count: {}'.format(event_count))
                        #    print('------------------------')
                        
                        print('Event Count: {}'.format(event_count))
                        print('------------------------')
                    
                    else:
                        continue


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        shutdown_and_report_stats()
