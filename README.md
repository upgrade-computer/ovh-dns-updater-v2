# ovh-dns-updater
Simple python script to update A/AAAA DNS records at OVH registrar 
Forked from : https://github.com/slowphil/ovh-dns-updater
Updated by : https://github.com/gigadjo


This script can maintain the A and/or AAAA DNS records (*)
of all your domains and subdomains hosted on the machine 
running this script, using OVH API. It is especially usefull it you are self-hosting and have only
a semi-permanent IP address with your ISP.

(* The script handles IPV4 and/or IPV6 addressing, given what
is available)

### Why yet another script for doing that?

There are tons of solutions for updating DNS records out there, and even pretty good ones.
For instance one could use this [dns updater](https://github.com/qdm12/ddns-updater),
or the dyndns client [ddclient](https://github.com/ddclient/ddclient). So why coming up with my own?

Well, OVH's DynHost implementation that ddclient uses is crippled as it cannnot:
- do multiple domain/subdomains with a single id set 
  (OVH's Dynhost requires separate logins per subdomain!).
- update AAAA records if you have ivp6 enabled 
  (OVH's DynHost supports ipv4 only).
  
And all OVH-API scripts I could find were not filling the bill for me. They are either unsuited or too heavy, complex universal tools.
For this task, I prefer a simple, easy to understand script that does little and that I can easily modify when needed.

If you have already created DynHost records in OVH, I believe the script would suppress them at the first update, but you can manually suppress them to be on the safe side. Alternatively, you can modify the script so that it 
 updates dynhost records, if you prefer.

## What this script does

The script queries the current *public* IP addresses
(V4 and V6) and checks the DNS A/AAAA records at OVH for all
domain/subdomains hosted on the machine (list defined as a dictionary in the script). 

If needed, the record is updated or created (You can add a new
subdomain this way).

If either IPV4 or IPV6 address is not available and if it is not indicated as required, then any corresponding
DNS record is suppressed (Otherwise your site will be unreachable with this ip version). Such situation presumably
arises because you disabled that ip version in your internet box (or your new
ISP does not offer it). 

Optionally, updating an IP addressing mode (4 or 6) can be disabled for
any given domain/subdomain (for intance, if you want it accessible
 _only_ in IPV4).

## Setting up

this script needs extra modules:
`pip install ovh requests`

In order to acccess the OVH API from this script, 
you need to generate API access keys 
at this site [https://eu.api.ovh.com/createToken/](https://eu.api.ovh.com/createToken/)  
(or use another access point relevant for your OVH subscription)

Provide your OVH login and password, a script name, a purpose,
a validity duration for the keys and ask for the four permissions:
```
GET /domain/zone/*
PUT /domain/zone/*
POST /domain/zone/*
DELETE /domain/zone/* (optionnal, since should rarely be useful)
```

With security in mind, if youre using a single OVH account, to manage multiples domains, authorisations should then be set as a 'per domain' basis : 

```
GET /domain/zone/
GET /domain/zone/example.ovh/*
PUT /domain/zone/example.ovh/*
POST /domain/zone/example.ovh/*
DELETE /domain/zone/example.ovh/*
```

This will allow the script to
- read the statuses of your domains/subdomains (GET)
- update records (PUT)
- create inexistent records and refresh (POST)
- delete record if the ipv6 or ipv4 address no longer exists

The keys delivered should be inserted in the ovh.conf file, next to the script.

Alternative ways to configure OVH Credentials : https://github.com/ovh/python-ovh#configuration

Other config parameters (domain names etc.) are setup directly inside the script. See explanations in the code.

### Config 'in code'

To configure script : 

- Edit the following part of the code :

```
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
```
This part configures domain names, and/or sub-domain for wich you want to create a record.
Let's walk trhough an example : you want to configure "host01.mydomain.tld" to Host01 IPv4 / IPv6 address,  and "*.host01.mydomain.tld" to point to Host01 IPv4 IP Address only.
Modify script as : 

```
hosts = [
        {
            "domain": "mydomain.tld", # Required
            "subdomain": "host01", # Required. Explicit subdomain or empty string "" (for @) or "*" for wildcard
            "ipv6": True, # Optional : maintain corresponding record, when possible
            "ipv4": True #explicitly disable modifiying ipv4 (A) records, even if public IPV4 exists (a possibly erroneous record would be left as-is)
            #"ttl": 60 # optional : if 'ttl' in specified in host, overrides the global default value 
        },
        {
            "domain": "host01.mydomain.tld",
            "subdomain": "*",
            "ipv4": True,
            "ipv6": False
            # 'ipv4' and 'ipv6' are not listed : automatically maintain any/both records, according to availability
        }
    ]
```

- If you want to use Host01 hostname (may it be "foo") as your subdomain, in case of automated deployment, or hostname change, do the following :

Import "socket" python module, uncomment (Line 10) : 
```
#import socket
```
change to : 
```
import socket
```
Activate "myhostname" variable, uncomment (Line 75)
```
#myhostname = socket.gethostname()
```
change to : 
```
myhostname = socket.gethostname()
```

Modify your hosts configuration as follow (Line 79)
```
hosts = [
        {
            "domain": "mydomain.tld", # Required
            "subdomain": "host01", # Required. Explicit subdomain or empty string "" (for @) or "*" for wildcard
            "ipv6": True, # Optional : maintain corresponding record, when possible
            "ipv4": True #explicitly disable modifiying ipv4 (A) records, even if public IPV4 exists (a possibly erroneous record would be left as-is)
            #"ttl": 60 # optional : if 'ttl' in specified in host, overrides the global default value 
        },
        {
            "domain": "host01.mydomain.tld",
            "subdomain": "*",
            "ipv4": True,
            "ipv6": False
            # 'ipv4' and 'ipv6' are not listed : automatically maintain any/both records, according to availability
        }
    ]
```
Change to : 
```
hosts = [
        {
            "domain": "mydomain.tld", # Required
            "subdomain": myhostname, # Required. Explicit subdomain or empty string "" (for @) or "*" for wildcard. myhostname, without quotes, if using it as a variable.
            "ipv6": True, # Optional : maintain corresponding record, when possible
            "ipv4": True #explicitly disable modifiying ipv4 (A) records, even if public IPV4 exists (a possibly erroneous record would be left as-is)
            #"ttl": 60 # optional : if 'ttl' in specified in host, overrides the global default value 
        }
    ]
```

### Run periodically with systemd
To run the updater automatically: 

- Edit ovh-dns-updater.service file :

```
[Unit]
Description=Check DNS records at OVH
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -u /absolute/path/to/ovh-dns-updater.py
#StandardOutput=journal+console
StandardOutput=file:/var/log/foo/stdout
StandardError=file:/var/log/foo/stderr
```
Let's suppose you cloned Git repo to /opt and want logs to be stored in /var/log/ovh-dns-updater/ : 

```
[Unit]
Description=Check DNS records at OVH
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -u /opt/ovh-dns-updater-v2/ovh-dns-updater.py
#StandardOutput=journal+console
StandardOutput=file:/var/log/ovh-dns-updater/stdout
StandardError=file:/var/log/ovh-dns-updater/stderr
```


copy (or link) the *ovh-dns-updater.timer* and *ovh-dns-updater.service* files in */etc/systemd/system* and run

```
systemctl enable ovh-dns-updater.timer
systemctl start ovh-dns-updater.timer
```

