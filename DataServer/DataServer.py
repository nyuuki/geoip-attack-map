#!/usr/bin/python3

"""
AUTHOR: Matthew May - mcmay.web@gmail.com
"""

# Imports
import json
import redis
import io
from sys import exit
from dbconst import META, PORTMAP, REDIS_IP, SYSLOG_PATH, DB_PATH, HQ_IP
from time import gmtime, localtime, sleep, strftime
import maxminddb
import itertools
from collections import defaultdict


# import logging
# import re
# from argparse import ArgumentParser, RawDescriptionHelpFormatter
# from os import getuid

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


def clean_db(unclean, src_or_dst):
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
            selected[src_or_dst + "_" + tag['lookup']] = head
    
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


def merge_dicts(*args):
    super_dict = {}
    for arg in args:
        super_dict.update(arg)
    return super_dict


# Create clean dictionary using unclean db dictionary contents
server_start_time = strftime("%d-%m-%Y %H:%M:%S", localtime())  # local time
event_count = 0
unknowns = defaultdict(int)
src_continents_tracked = defaultdict(int)
src_countries_tracked = defaultdict(int)
src_ips_tracked = defaultdict(int)
dst_continents_tracked = defaultdict(int)
dst_countries_tracked = defaultdict(int)
dst_ips_tracked = defaultdict(int)
country_to_code = {}
ip_to_code = {}


def track_flags(super_dict, tracking_dict, key1, key2):
    if key1 in super_dict and key2 in super_dict and key1 not in tracking_dict:
        tracking_dict[super_dict[key1]] = super_dict[key2]


def track_stats(super_dict, tracking_dict, key):
    node = super_dict.get(key, False)
    if node is not False:
        tracking_dict[node] += 1
    else:
        unknowns[key] += 1


def to_json(syslog_data_dict):
    src_ip_db_unclean = parse_maxminddb(syslog_data_dict['src_ip'])
    dst_ip_db_unclean = parse_maxminddb(syslog_data_dict['dst_ip'])
    
    if src_ip_db_unclean and dst_ip_db_unclean:
        global event_count, ip_to_code, country_to_code, unknowns, \
            src_continents_tracked, src_countries_tracked, src_ips_tracked, \
            dst_continents_tracked, dst_countries_tracked, dst_ips_tracked
        
        msg_type = {'msg_type':get_msg_type()}
        msg_type2 = {'msg_type2':syslog_data_dict['type_attack']}
        msg_type3 = {'msg_type3':syslog_data_dict['cve_attack']}
        proto = {'protocol':get_tcp_udp_proto(
                syslog_data_dict['src_port'],
                syslog_data_dict['dst_port']
        )}
        
        super_dict = merge_dicts(
                syslog_data_dict, msg_type, msg_type2, msg_type3, proto,
                clean_db(src_ip_db_unclean, src_or_dst="src"),
                clean_db(dst_ip_db_unclean, src_or_dst="dst"),
        )
        
        # Track Stats
        event_count += 1
        event_time = strftime("%d-%m-%Y %H:%M:%S", localtime())  # local time
        # event_time = strftime("%Y-%m-%d %H:%M:%S", gmtime()) # UTC time
        # Append stats to super_dict
        super_dict['event_count'] = event_count
        super_dict['event_time'] = event_time
        super_dict['unknowns'] = unknowns
        
        track_stats(super_dict, src_continents_tracked, 'src_continent')
        track_stats(super_dict, dst_continents_tracked, 'dst_continent')
        track_stats(super_dict, src_countries_tracked, 'src_country')
        track_stats(super_dict, dst_countries_tracked, 'dst_country')
        track_stats(super_dict, src_ips_tracked, 'src_ip')
        track_stats(super_dict, dst_ips_tracked, 'dst_ip')
        
        for src_or_dst, val_type in itertools.product(["src_", "dst_"], [
            "continents_tracked", "countries_tracked", "ips_tracked"]):
            key = src_or_dst + val_type
            super_dict[key] = globals()[key]
        
        track_flags(super_dict, country_to_code, 'src_country', 'src_iso_code')
        track_flags(super_dict, country_to_code, 'dst_country', 'dst_iso_code')
        super_dict['country_to_code'] = country_to_code
        
        track_flags(super_dict, ip_to_code, 'src_ip', 'src_iso_code')
        track_flags(super_dict, ip_to_code, 'dst_ip', 'dst_iso_code')
        super_dict['ip_to_code'] = ip_to_code
        
        json_data = json.dumps(super_dict)
        return json_data
    else:
        return


def main():
    # if getuid() != 0:
    #    print('Please run this script as root')
    #    print('SHUTTING DOWN')
    #    exit()
    
    # args = menu()
    
    # Connect to Redis
    redis_instance = connect_redis()
    # Find HQ lat/long
    # hq_dict = find_hq_lat_long()
    
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
                if not syslog_data_dict:
                    continue
                json_data = to_json(syslog_data_dict)
                if not json_data:
                    continue
                redis_instance.publish('attack-map-production', json_data)
                
                # if args.verbose:
                #    print(ip_db_unclean)
                #    print('------------------------')
                #    print(json_data)
                #    print('Event Count: {}'.format(event_count))
                #    print('------------------------')
                print('Event Count: {}'.format(event_count))
                print('------------------------')


def shutdown_and_report_stats():
    print('\nSHUTTING DOWN')
    # Report stats tracked
    print('\nREPORTING STATS...')
    print('\nEvent Count: {}'.format(event_count))  # report event count
    print('\nContinent Stats...')  # report continents stats
    for key in src_continents_tracked:
        print('{}: {}'.format(key, src_continents_tracked[key]))
    print('\nCountry Stats...')  # report country stats
    for country in src_countries_tracked:
        print('{}: {}'.format(country, src_countries_tracked[country]))
    print('\nCountries to iso_codes...')
    for key in country_to_code:
        print('{}: {}'.format(key, country_to_code[key]))
    print('\nIP Stats...')  # report IP stats
    for ip in src_ips_tracked:
        print('{}: {}'.format(ip, src_ips_tracked[ip]))
    print('\nIPs to iso_codes...')
    for key in ip_to_code:
        print('{}: {}'.format(key, ip_to_code[key]))
    print('\nUnknowns...')
    for key in unknowns:
        print('{}: {}'.format(key, unknowns[key]))
    exit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        shutdown_and_report_stats()
