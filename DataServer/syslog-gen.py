#!/usr/bin/python3

# import random, syslog
import random
from dbconst import PORTMAP, SYSLOG_PATH
from sys import exit
from time import sleep
import datetime
from random import randint


def main():
    port_list = []
    type_attack_list = []
    
    ip_type_list = [4]
    
    for port in PORTMAP:
        port_list.append(port)
        type_attack_list.append(PORTMAP[port])
    
    while True:
        dst_port = random.choice(port_list)
        src_port = randint(49152, 65535)
        
        iptype = random.choice(ip_type_list)
        if iptype == 4:
            src_addr = '.'.join([str(randint(0, 255)) for x in range(4)])
            dst_addr = '.'.join([str(randint(0, 255)) for x in range(4)])
            # src_addr = random.choice(["203.0.113.1", "203.0.113.2", "11.11.11.11"])
            # dst_addr = random.choice(["203.0.113.3", "203.0.113.4"])
        # else:
        #    src_addr = ':'.join([hex(randint(2 ** 16, 2 ** 17))[-4:] for x in range(8)])
        #    dst_addr = ':'.join([hex(randint(2 ** 16, 2 ** 17))[-4:] for x in range(8)])
        
        type_attack = random.choice(type_attack_list)
        cve_attack = 'CVE:{}:{}'.format(
                random.randrange(1, 2000),
                random.randrange(100, 1000))
        rand_data = '{},{},{},{},{},{}'.format(
                src_addr, dst_addr, src_port, dst_port, type_attack, cve_attack)
        
        now = datetime.datetime.now()
        str_time = now.strftime('%H:%M:%S')
        str_month_name = now.strftime('%b')
        # Mar  3 19:32:23 ubuntu /syslog-gen.py:
        with open(SYSLOG_PATH, "a") as f:
            f.write("Mar  {2} {0} ubuntu {3}: {1}\n".format(
                    str_time, rand_data, now.day, str_month_name, __file__))
        # syslog.syslog(rand_data)
        print(rand_data)
        sleep(random.choice([0.3, 1, 0.8]))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
