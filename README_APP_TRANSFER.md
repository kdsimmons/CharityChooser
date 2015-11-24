# Switching between local and AWS versions of app
This document is mainly for my own reference when transferring code between AWS and my local machine.

## Moving files
#### On source
<pre>zip -r app_DDDD.zip app</pre>

#### Local --> AWS
<pre>transup app_DDDD.zip</pre>

#### AWS --> local
<pre>transdown app_DDDD.zip</pre>

#### On destination
<pre>unzip -o app_DDDD.zip</pre>

## Changing filenames
#### On either version, above app directory
<pre>. ChangePaths.sh</pre>

#### Local only
<pre>cp myapp_local.conf myapp.conf</pre>

#### AWS only
<pre>cp myapp_aws.conf myapp.conf</pre>

## Converting mySQL database
#### SQL --> dump
<pre>mysqldump -u sqluser -p charity_data > dumpcharity.sql</pre>

#### dump --> SQL
<pre>
mysql -u sqluser -p create database charity_data
mysql -u sqluser -p charity_data < dumpcharity.sql
</pre>
