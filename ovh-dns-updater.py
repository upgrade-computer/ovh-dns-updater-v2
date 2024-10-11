#!/usr/bin/env python
# -*- encoding: utf-8 -*-


import json
import ovh
import sys
import requests, time
#to use 'hostname as subdomain, impot socket module:
#import socket


'''
API credentials
can be provided in variety of ways:
(see https://github.com/ovh/python-ovh#configuration)
-explicitly here :
'''
#client = ovh.Client(
#        endpoint           = "ovh-eu",
#        application_key    = "XXXXXXXXXXXXXXXX",
#        application_secret = "YYYYYYYYYYYYYYYY",
#        consumer_key       = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
#        )
'''
-or in the ENVIRONMENT 
-or in a ovh.conf file
in which cases we can call with no argument (the ovh module gets the credentials on its own):

file ovh.conf eg :
[default]
; general configuration: default endpoint
endpoint=ovh-eu

[ovh-eu]
; configuration specific to 'ovh-eu' endpoint
application_key=my_app_key
application_secret=my_application_secret
consumer_key=my_consumer_key

file location defaults : Current working directory: ./ovh.conf
Current user's home directory ~/.ovh.conf
System wide configuration /etc/ovh.conf
'''
client = ovh.Client()

# Should missing IP address being considered as error (Depend on the ISP, internet box settings...)?
# In case a required IP cannot be obtained, the script will send an email and stop without updating anything. 
# If, for any reason, IPv4 or IPv6 address cannot be obtained and if it is not protected by this list, the corresponding records will be deleted for all hosts.
#ip_versions_required = [4] # MUST not be empty. Can be [4],[6] or [4,6] 
ip_versions_required = [6] 
default_ttl =  600  # seconds
# ttl = how long will a DNS server cache the value before checking it at the Registrar. Longer value yields faster name resolution most of the time, but less frequent updates

# list of hosts (=subdomain.domain.tld) to update, each a dictionnary with at least "domain" and "subdomain" defined
# Exemple : 
#hosts = [
#        {
#           "domain": "exemple.ovh",
#           "subdomain": "myhost", or "", (for @) or "*", for wildcard
#           "ipv6": "True", / "False",
#           "ipv4": "True", / "False",
#           "ttl": "60" - "3600"
#        },
#        {
#           "domain": "mydomain.ovh",
#           "subdomain": "myhost", or "", (for @) or "*", for wildcard
#           "ipv6": "True", / "False",
#           "ipv4": "True", / "False",
#           "ttl": "60" - "3600"
#        }
#    ]
#

#myhostname = socket.gethostname()
#you can use myhostname (without ") as subdomain, if you wish to create an host record like : $HOSTNAME.mydomain.tld
#usefull if you bring up a lot of devices :-)

hosts = [
        {
            "domain": "mydomain.tld", # Required
            "subdomain": "www", # Required. Explicit subdomain or empty string "" (for @) or "*" for wildcard
            #"ipv6": any_value_except_False # Optional : maintain corresponding record, when possible
            "ipv4": False, #explicitly disable modifiying ipv4 (A) records, even if public IPV4 exists (a possibly erroneous record would be left as-is)
            #"ttl": 60 # optional : if 'ttl' in specified in host, overrides the global default value 
        },
        {
            "domain": "otherdomain.tld",
            "subdomain": ""
            # 'ipv4' and 'ipv6' are not listed : automatically maintain any/both records, according to availability
        }
    ]

checkDNS_interval_hrs = 12.1 # when the saved IP addresses are old, check the DNS record, even if the addresses did not change
#save last known address in local file.
current_ip_file = "/tmp/current_ip.json"


def send_email(msg, sender = 'no_reply@mydomain.com', receiver = 'admin@mydomain.com', yourname = 'Your Name', SMTPuser = 'user@mydomain.com', SMTPpass = 'my_secure_pass') :
  import smtplib

  try :
     smtpObj = smtplib.SMTP(host='smtp.mydomain.com', port='587')
     smtpObj.ehlo()
     smtpObj.starttls()
     smtpObj.login(SMTPuser,SMTPpass)
     smtpObj.sendmail("From: {}\nTo: {}\nSubject: DNS update problem\n\nThe ovh-dns-updater.py script reports:\n{}\n".format(sender, receiver, msg))
     smtpObj.quit()
     print (timestamp()," : DNS Update Problem : email successfully sent!")

  except smtplib.SMTPException:
     print (timestamp()," : Error unable to send DNS Update Problem email" % str(error))
     print (timestamp()," : Unable to send Email" % str(error))
          

#If You whish to use 'localhost' configured SMTP, you can use this code instead)
#def send_email(msg, sender = 'no_reply@mydomain.com', receiver = 'admin@mydomain.com') :
#  import smtplib
#
#  try :
#     smtpObj = smtplib.SMTP('localhost')
#     smtpObj.sendmail(sender, receiver,
#         "From: {}\nTo: {}\nSubject: DNS update problem\n\nThe ovh-dns-updater.py script reports:\n{}\n".format(sender, receiver, msg)
#         )
#  except smtplib.SMTPException:
#     print( timestamp()," : Error unable to send email")

def get_current_ip(v = 4):
    if v == 4 :
        url_list = ["https://api.ipify.org", "https://ipv4.lafibre.info/ip.php", "https://v4.ident.me"]
    else :
        url_list = ["https://api6.ipify.org", "https://ipv6.lafibre.info/ip.php", "https://v6.ident.me"]
    ip = ""
    message = ""
    for url in url_list :
        try :
            r = requests.get(url, timeout=30.0)
        except requests.exceptions.RequestException as e:
            message += "failed getting ipv{} address from {} because {} occurred\n".format(v, url, str(e))
            continue
        if r.status_code == requests.codes.ok :
            ip = r.text
            break
        else : 
            message += "{} : Cannot get IPv{} from {}: requests.get returned status_code {}.\n".format(timestamp(), v, url, r.status_code)
    if ip != "":
        return ip
    elif v in ip_versions_required :
            message += "Failed getting required IPv{}. There is most likely a real connectivity problem. Aborting". format( v)
            print(message)
            send_email (message)
            quit()
    else :
        return False




def timestamp() :
    return time.asctime( time.localtime(time.time()) )

def update_record(domain, subdomain, new_ip, _ttl = 600):
    #Update the (A or AAAA) record with the provided IP

    global records_changed
    typ = 'AAAA' if ":" in new_ip else 'A'
    #print("checking record {} for {}.{}".format(typ,subdomain,domain))
    path = "/domain/zone/{}/record".format(domain)
    result = client.get(path,
                        fieldType = typ,
                        subDomain = subdomain
                     )

    if len(result) != 1:
        #creating NEW record
        result = client.post(path,
                    fieldType = typ,
                    subDomain = subdomain,
                    target = new_ip,
                    ttl = _ttl
                     )
        client.post('/domain/zone/{}/refresh'.format(domain))
        result = client.get(path,
                        fieldType=typ,
                        subDomain=subdomain
                        )
        record_id = result[0]
        records_changed += 1
        print("{} : ### created new record {} for {}.{}".format(timestamp(),typ,subdomain,domain))
    else :
        # record exists
        record_id = result[0]
        path = "/domain/zone/{}/record/{}".format(domain,record_id)
        result = client.get(path)
        oldip = result['target']
        #print('record exists, with ip :',oldip)
        if oldip == new_ip :
            #print('nothing to do')
            return
        else :
            #print('updating to ', new_ip)
            result = client.put(path,
                subDomain = subdomain,
                target = new_ip,
                ttl = _ttl
                 )
            client.post('/domain/zone/{}/refresh'.format(domain))
            records_changed += 1
    #checking changes
    result = client.get("/domain/zone/{}/record/{}".format(domain,record_id))
    if new_ip != result['target'] :
        records_changed -= 1
        raise Exception("Error updating {}.{} with {}".format(subdomain,domain,new_ip))


def delete_record(domain, subdomain, typ):
    """
    if it exists, delete an A or AAAA record
    (because the corresponding IP is not available)
    """
    #print("checking record {} for {}.{}".format(typ,subdomain,domain))
    global records_changed
    result = client.get("/domain/zone/{}/record".format(domain),
                        fieldType = typ,
                        subDomain = subdomain
                     )
    if len(result) == 1:
        # record exists, delete it
        record_id = result[0]
        print("{} : ### deleting record {} for {}.{}".format(timestamp(),typ,subdomain,domain))
        client.delete("/domain/zone/{}/record/{}".format(domain,record_id))
        client.post('/domain/zone/{}/refresh'.format(domain))
        records_changed += 1


current_ipv4 = get_current_ip(4)
current_ipv6 = get_current_ip(6)
#print('current ips: {} ; {}'.format(current_ipv4, current_ipv6))

#reload saved values & compare
try:
    with open(current_ip_file, 'r') as f:
        old_time, old_ipv4, old_ipv6   = json.load(f)
    need_update = (old_ipv4 != current_ipv4) or (old_ipv6 != current_ipv6) or ((old_time - time.time()) > 3600.0 * checkDNS_interval_hrs)
except IOError:
    #print("No old ips recorded")
    need_update = True
if need_update :
  records_changed = 0
  try :
    for host in hosts :
      domain = host["domain"]
      subdomain = host ["subdomain"]
      if ('ipv4' not in host) or (host['ipv4'] != False) :
          if current_ipv4 :
              ttl = default_ttl if ('ttl' not in host) else host['ttl']
              update_record(domain, subdomain, current_ipv4, _ttl = ttl)
          else :
              delete_record(domain, subdomain, 'A')
      else :
          #print("Not touching A record for {}.{}, as instructed".format(subdomain, domain))
          pass
      if ('ipv6' not in host) or (host['ipv6'] != False) :
          if current_ipv6 :
              ttl = default_ttl if ('ttl' not in host) else host['ttl']
              update_record(domain, subdomain, current_ipv6, _ttl = ttl)
          else :
              delete_record(domain, subdomain, 'AAAA')
      else :
          #print("Not touching AAAA record for {}.{}, as instructed".format(subdomain, domain))
          pass
    #all hosts records have been updated without errors, log change and save current addresses
    print("{} : new addresses {} ; {} -- {} records updates".format(timestamp(), current_ipv4, current_ipv6, records_changed))
    with open(current_ip_file, 'w') as f:
      json.dump([time.time(), current_ipv4, current_ipv6],f)
  except Exception as e: #some error occured (API down, keys expired...?),
    msg = "{} : ### error {} while updating records!! {} records updated with new addresses {} ; {}".format(timestamp(),  str(e), records_changed, current_ipv4, current_ipv6)
    print(msg)
    send_email(msg)
    # not saving new addresses, so that update is attempted again.
else :
  #print("nothing to do!")
  pass


