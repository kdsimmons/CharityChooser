# CharityChooser

The CharityChooser repo contains the code behind my website at http://www.kristinadsimmons.com/charitychooser. I created this website as part of my fellowship with Insight Health Data Science during July 2015.

CharityChooser was created to provide a site where users can find a list of charitable organizations targeting a specific disease that fit their personal preferences.  For more information, see my [slide deck](https://docs.google.com/presentation/d/1zMyeldkEXbL4pYDvbZ2W9nXYbI4kKLzNJOWwDQFYMOU/pub?start=false&loop=false&delayms=3000#slide=id.gc41fb56fb_0_0).

## Create the database

These files are run once to build the database of charities.

0. [Note: do 'sudo mysqld_safe' from command line first.]
1. make_database.py: main script to scrape data and build SQL database
1. get_distributions.py: functions to create table of summary statistics
1. master_disease_list.py: utility to load in list of diseases

## Run the website

These files are run in real time whenever someone visits the website.

* Python code
  * \__init__.py: wrapper to implement Flask
  * views.py: outer code to run app
  * program_rankings.py: functions to rank charities
* Supervisor server 
  * start_app: command to start running app with supervisor
  * myapp.conf: supervisord configuration
  * supervisord.log, supervisord.pid: info printed by supervisord
* templates directory: HTML templates
* static directory: CSS, JS, and font files needed to run website


**Copyright 2015 Kristy Simmons**

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
