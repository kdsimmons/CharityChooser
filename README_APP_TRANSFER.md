# Switching between local and AWS versions of app
This document is mainly for my own reference when transferring code between AWS and my local machine.

## Moving files
#### On source
<pre>zip -r app_DDDD.zip app</pre>

#### Local --> AWS
transup app_DDDD.zip

#### AWS --> local
transdown app_DDDD.zip

#### On destination
unzip -o app_DDDD.zip

## Changing filenames
#### On either version, above app directory
. ChangePaths.sh

### Local only
cp myapp_local.conf myapp.conf

### AWS only
cp myapp_aws.conf myapp.conf

## Converting mySQL database
### SQL --> dump
mysqldump -u sqluser -p charity_data > dumpcharity.sql

### dump --> SQL
mysql -u sqluser -p create database charity_data
mysql -u sqluser -p charity_data < dumpcharity.sql
