#!/usr/bin/python
import urllib2
import time
import os


'''
Parameters:
Number of attached probes to EM1 module located at wall near unusable lab doors
Internet address of EM1 module (set with extra putty)
File to save to
'''
number_of_probes = 4
IP = '10.97.112.15'

timestamp = time.localtime()
year = str(timestamp[0])
month = str(timestamp[1])
day = str(timestamp[2])

storefile = year + '-' + month + '-' + day + '-' +'temp.dat'

path ='data' + '/' + 'temperature_data' + '/' + year + '/' + '/' + month
epochtime = time.time()

if not os.path.exists(path):
    os.makedirs(path)

os.chdir(path)

f = open(storefile, 'a+')
data = urllib2.urlopen('http://'+ IP + '/data')
data = data.read()
data = data.split('|')
temparray = []
for i in range(number_of_probes):
    tempindex = i*3 + 1
    temp = str(data[tempindex])
    f.write(temp + ',')
f.write(str(epochtime) + '\n')
f.close
