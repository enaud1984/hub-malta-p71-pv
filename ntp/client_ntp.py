import ntplib
from time import ctime
c = ntplib.NTPClient()
response = c.request('10.1.64.152')
print(ctime(response.tx_time))