# Importing all the required libraries
import bs4 as bs
import urllib.request
import queue
import threading
import time
import csv
import json
from datetime import datetime

# Printing the time when program started
print('starting at {}'.format(datetime.now()))

# Defining all global variables
start = 1
stop = 2000
filename = "Waterbill-{}.csv".format(stop)

fields = ["active_flag","deprecated_consumer_id","consumer_id",
           "consumer_name","address","connection_type","flat_count",
           "connection_date","socio_economic_group","ward","connection_size",
           "remarks","current_meter_installation_date","pcmc_mi","phone",
           "email","mobile","meter_no","user_name","location","metered",
           "billing_frequency","due_amount"]

records = []

# Scraping the data

class myThread (threading.Thread):
   def __init__(self, i):
      threading.Thread.__init__(self)
      self.i = i
   def run(self):
       
        try:
            i=self.i
            url = 'http://103.224.247.125:26000/public/consumer/searchonlinePayment/{}'.format(i)
                
            sauce = urllib.request.urlopen(url, timeout = 50).read()
            soup = bs.BeautifulSoup(sauce, 'lxml')
                
            data = soup.p.get_text()
            consumer = json.loads(data)['consumer']

            # Handeling newline and carriage return in address section of data
            if '\n' in consumer['address']:
                consumer['address'] = consumer['address'].replace('\n', '')
            if '\r' in consumer['address']:
                consumer['address'] = consumer['address'].replace('\r', '')
                
            billing_url = 'http://103.224.247.125:26000/public/consumer/balance/{}'.format(i)
            
            billing_sauce = urllib.request.urlopen(billing_url, timeout = 50).read()
            billing_soup = bs.BeautifulSoup(billing_sauce, 'lxml')
            
            due_amount = json.loads(billing_soup.p.get_text())['balance']

            consumer['due_amount'] = due_amount 
                
            records.append(consumer)
            print('processing {} record'.format(i))
        except Exception as error:
            print('An exception occured for {} retrying \n'.format(i))
            #for restarting operation if failed
            time.sleep(1)
            tr=myThread(self.i)
            tr.start()
            tr.join()

threads = []
j=0
#cheange(increase) this if you want to increase speed // or reduce this value if   connection attempt failed
breakafterthreads=45
#creating and starting threads
for tName in range(start,stop+1):

    thread = myThread(tName)
    thread.start()
    threads.append(thread)
    j=j+1
    if(j==breakafterthreads):
	    time.sleep(1)
    if(j==breakafterthreads):
        j=0

        

#joining threads to main thread 
for t in threads:
   t.join()

# writing to csv file 
with open(filename, 'w', encoding='utf8') as csvfile: 
    # creating a csv dict writer object 
    writer = csv.DictWriter(csvfile, fieldnames = fields, delimiter='|') 
      
    # writing headers (field names) 
    writer.writeheader() 
      
    # writing data rows 
    writer.writerows(records)

# Printing the finish time for program.

print('Finished at {} with {} records'.format(datetime.now(),records.__len__()))
