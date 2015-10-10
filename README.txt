CharityChooser

README.txt: this document
README.md: markdown from github

misc. files:
FarmersMarketsBenefits.json
Farmers_Markets_With_Benefits.csv: Boston farmers market list
git_notes: notes from git tutorial during dev setup
Insight_Test_DC.csv, Insight_Train_DC.csv: data for data challenge from 8/11
KDSWeek2.pdf: week 2 presentation
KristySimmonsInsightDemo.pdf: presentation for demos
Kristy_Simmons_Week1.pdf: week 1 presentation
OutreachIdeas.txt: ideas for project focused on outreach
python_notes.txt: misc notes on Python
ProjectIdeas.txt: ideas for data project
PutPandasInMySQL.txt: script to put data in SQL for sharing
sql_practice.sql: code to practice using SQL
test_db.py: test that MySQL is working
timing.txt: timing of each slide
world_innodb.sql: SQL file from dev setup

data analysis files (some in app folder):
AvailableInfo.txt: variables available from BBB and CN
clean_sql.py: clean SQL database without rescraping (duplicate of code to make_database.py used when changes are made to the cleaning process)
DataFromAdam: files from previous fellow who looked at charities
get_distributions.py: make SQL database with distributions of features so that app runs faster
give_org_html.txt: HTML copied into text file for Week 1 presentation
make_database.py: python script to get data for all diseases using main function (previously called charities.py)
master_disease_list.py: load all diseases searched
project_week2.py: old python script to get data for a specified disease (no longer useful)
validation2_data.csv, validation2_results.csv: results from validation
week2_run.sh: old shell script to run through diseases collecting data (no longer useful)

ipython notebooks:
10 Minutes to pandas.ipynb: tutorial on pandas module
Insight_DC_Workbook.ipynb: Adam's code for his data challenge from 8/11
clean_sql.ipynb: clean SQL database that's already been created
colon_cancer.ipynb: full analysis of colon cancer charities
convert_to_mysql.ipynb: work toward getting data into SQL
customize_search.ipynb: work on tailoring measurement to user specification
data_challenge.ipynb: data challenge from 8/11
facebook_twitter.ipynb: work toward getting facebook and twitter results
first_analysis.ipynb: old analysis of farmers markets
get_char_nav_data.ipynb: work on scraping Charity Navigator
hashing.ipynb: practice with hash tables
hiv_cleavage.ipynb: practice data challenge
initial_from_csv.ipynb: old script for farmers market list 
interview_practice.ipynb: misc code to prep for interviews
learning_beautiful_soup.ipynb: practice with beautiful soup
look_at_data.ipynb: exploratory data analysis
machine_learning_practice.ipynb: practice doing machine learning
make_graphs.ipynb: make graphs and do basic clustering for Week 2
multiple_sclerosis.ipynb: work for week 1 presentation
practice_scraping.ipynb: practice scaping based on tutorial
project_week2.ipynb: clean code from week 2
project_week3.ipynb: clean code from week 3
scraping_databases.ipynb: work toward scraping charity websites
scraping_scratch_work.ipynb: notebook for testing out new web scraping code
scratch_work.ipynb: space for testing out code
validation_ver1.ipynb: project validation
validation_ver2.ipynb: project validation

app files in this directory:
ChangePaths.sh: change paths after downloading files from AWS 
app*loc.zip: zipped folder ready for transfer to AWS
app*aws.zip: zipped folder tranfered from AWS
dumpcharity.sql: SQL database for transfer to/from AWS
run.py: main file to execute project app (no longer used)

app files in app directory:
__init__.py,__init__.pyc: use Flask
framework_views.py: obsolete
get_distributions.py: save info on feature distributions
make_database.py: get data
master_disease_list.py,master_disease_list.pyc: load in list of diseases
master_disease_list.txt: obsolete
myapp.conf: supervisord configuration
program_rankings.py,program_rankings.pyc: functions to rank charities
start_app: command to start running app with supervisor
supervisord.log,supervisord.pid: info printed by supervisord
views.py,views.pyc: outer code to run app

static: CSS, JS, and font files needed to run website

templates: HTML templates for website


