#!/usr/bin/env python

import pandas as pd
import bs4
import re, numpy as np
import matplotlib.pyplot as plt
import requests, urllib2
import tweepy
import pymysql as mdb
import sys
import master_disease_list
import urlparse

def scrape_bbb_urls(disease):
    # import URL into beautiful soup object

    dis_as_str = '+'.join(disease.split())
    base_url = "http://give.org"
    give_org_url = base_url + "/search/?term=" + dis_as_str + "&location=&FilterAccredited=false&tobid="
    
    bbb_soups = []

    # loop through all pages of search results
    more_pages = True 
    while(more_pages):
        response = requests.get(give_org_url)
        soup = bs4.BeautifulSoup(response.text)
        bbb_soups.append(soup)
        next_link = soup.select('a[href*=search/?page]')
        
        more_pages = False
        for link in next_link:
            if re.findall('.*Next.*', link.getText()):
                give_org_url = base_url + link.attrs['href']
                more_pages = True

    return bbb_soups

def clean_bbb_info(bbb_soups,disease):
    # pull out charity links and info
    # NOTE: May need permission to include links to BBB. I didn't find any info on restrictions in pulling information.
    charities = []
    for soup in bbb_soups:
        tables = soup.select('div.search table')
        if len(tables) == 0:
            print "No charities found."
            return charities
            # TO DO: make this an error code instead of continuing to run
        bbb_table = tables[0].tbody 
        for row in bbb_table.findAll('tr'):
            charity_data = {}
            charity_data['disease'] = disease
            charity_data['name'] = row.select('a.charity-link')[0].get_text().replace(u'\u2019', u'\'')
            charity_data['bbb_link'] = row.select('a.charity-link')[0].attrs.get('href')
            accred_seal = row.select('img.charity-search-seal')
            if accred_seal:
                charity_data['bbb_accred'] = accred_seal[0].attrs.get('alt')
            else:
                charity_data['bbb_accred'] = row.select('div.accreditation-mobile')[0].get_text()
            charity_data['address'] = row.select('div.accreditation-mobile')[0].next_sibling.strip('" ').replace(u'\u2019', u'\'')
            charity_data['city'] = row.select('div.accreditation-mobile')[0].next_sibling.next_sibling.next_sibling.strip('" ')
            
            charities.append(charity_data)

    # get other data from BBB where possible
    for charity in charities:
        response = requests.get(charity['bbb_link'])
        soup = bs4.BeautifulSoup(response.text)
        
        # year of incorporation and stated purpose 
        try:
            purpdiv = soup.select('div#purpose')[0]
            tag = purpdiv.findNext(text=re.compile('Year, State Incorporated'))
            charity['year_incorporated'] = int(re.findall('[1-2][0-9][0-9][0-9]', tag.findNext('p').text)[0])
        except:
            charity['year_incorporated'] = -1
        try:
            tag = purpdiv.findNext(text=re.compile('Stated Purpose'))
            charity['purpose'] = tag.findNext('p').replace(u'\u2019', u'\'').text.strip('" ')
        except:
            charity['purpose'] = ''

        # board and staff size
        try:
            govdiv = soup.select('div#governance')[0]
            charity['board_size'] = govdiv.findNext(text=re.compile('Board Size')).findNext('p').text
            charity['staff_size'] = govdiv.findNext(text=re.compile('Paid Staff Size')).findNext('p').text
        except:
            charity['board_size'] = -1
            charity['staff_size'] = -1

        # tax exempt status
        try:
            taxdiv = soup.select('div#taxstatus')[0]
            charity['tax_status'] = taxdiv.findNext('p').text.replace(u'\u2019', u'\'')
        except:
            charity['tax_status'] = 'unknown'

    return charities


def get_charity_links(charities):
    # Use BBB pages to get links to each charity's website
    
    for charity in charities:
        soup = bs4.BeautifulSoup(requests.get(charity['bbb_link']).text)
        if len(soup.select('div.charity-contact')) > 0:
            charity['link'] = soup.select('div.charity-contact')[0].a.attrs.get('href')
        elif len(soup.select('div.charity-detail-text')) > 0:
            charity['link'] = soup.select('div.charity-detail-text')[0].a.attrs.get('href')
        elif len(soup.select('a#ctl00_ContentPlaceHolder1_aWebUrl')) > 0:
            charity['link'] = soup.select('a#ctl00_ContentPlaceHolder1_aWebUrl')[0].attrs.get('href')
        else:
            charity['link'] = ''
    # TO DO: should add text search for websites printed as text rather than link
    
    return charities

def scrape_social_media(charities):
    # Find Facebook likes and Twitter followers for each charity
    # TO DO: Find the right FB/Twitter account, e.g. for National MS Society chapters.
    for charity in charities:
        if charity['link'] == '':
            charity['facebook_link'] = ''
            charity['twitter_link'] = ''
        else: 
            try:
                page = urllib2.urlopen(urllib2.Request(charity['link'], headers={'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'}))
                target_soup = bs4.BeautifulSoup(page.read(), 'html.parser')
            except:
                #print charity['name']
                charity['facebook_link'] = ''
                charity['twitter_link'] = ''
                continue
    
            try:
                fblink = target_soup.select('a[href*=facebook.com]')[0].attrs.get('href')
            except IndexError:
                fblink = ''
            charity['facebook_link'] = fblink 
            
            try:
                twlink = target_soup.select('a[href*=twitter.com]')[0].attrs.get('href')
            except IndexError:
                twlink = ''
            charity['twitter_link'] = twlink

            donlinks = target_soup.findAll('a')
            charity['donate_link'] = ''
            for link in donlinks:
                if re.findall('Donate|Donation|Contribute', str(link), re.IGNORECASE):
                    url = link.attrs.get('href')
                    if url:
                        res = urlparse.urlparse(url)
                        if not res.scheme == '': # check whether this is a full link
                            charity['donate_link'] = url
                            break
            
    return charities

def get_twitter_followers(charities):
    # import authorization info 
    twauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/twitter_access.csv')
    auth = tweepy.OAuthHandler(twauth.consumer_key['twitter'], twauth.consumer_secret['twitter'])
    auth.set_access_token(twauth.access_token['twitter'], twauth.access_secret['twitter'])
    
    api = tweepy.API(auth)
    
    for charity in charities:
        if charity['twitter_link'] == '':
            charity['twitter_followers'] = -1
        else:
            try:
                twitterid = re.findall('http[s]*://twitter.com/(.*)', charity['twitter_link'])[0]
                user = api.get_user(twitterid)
                charity['twitter_followers'] = user.followers_count
            except:
                charity['twitter_followers'] = -1
                continue
                
    return charities


def get_char_nav_info(dictlist): 
    for charity in dictlist:
        # get link to Charity Navigator's website on this charity
        words = '+'.join(charity['name'].split())
        url = ('https://www.charitynavigator.org/index.cfm?keyword_list=' + words 
               + '&nameonly=1&Submit2=Search&bay=search.results')
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text)
        if len(soup.select('p.rating')) > 0:
            charity['cn_link'] = soup.select('p.rating')[0].a.attrs.get('href')
            charity['cn_rated'] = 'Rated'
        else:
            url = ('https://www.charitynavigator.org/index.cfm?keyword_list=' + words 
                   + '&nameonly=1&Submit2=Search&bay=search.results2')
            response = requests.get(url)
            soup = bs4.BeautifulSoup(response.text)
            if len(soup.select('p.orgname')) > 0:
                charity['cn_link'] = soup.select('p.orgname')[0].a.attrs.get('href')
                charity['cn_rated'] = 'Unrated'                
            else:
                print charity['name'] + ": No Charity Navigator link."
                charity['cn_link'] = ''
                charity['cn_rated'] = ''
            charity['cn_overall'] = -1.
            charity['cn_financial'] = -1.
            charity['cn_acct_transp'] = -1.
            charity['leader_compensation'] = ''
            charity['total_contributions'] = -1
            charity['total_expenses'] = -1
            charity['total_revenue'] = -1
            charity['percent_admin'] = -1.
            charity['percent_fund'] = -1.
            charity['percent_program'] = -1.
            charity['ein'] = ''
            continue
        
        # get Charity Navigator data 
        charsoup = bs4.BeautifulSoup(requests.get(charity['cn_link']).text)
        
        overall_tags = charsoup.findAll('strong', text='Overall')
        fin_tags = charsoup.findAll('strong', text=re.compile('\WFinancial'))
        acct_tags = charsoup.findAll('strong', text=re.compile('\WAccountability & Transparency'))
        
        # include overall rating
        if len(overall_tags) >= 1:
            charity['cn_overall'] = float(overall_tags[0].parent.nextSibling.nextSibling.text)
        else:
            print charity['name'] + ": No Overall cells."
            charity['cn_overall'] = -1.
        # include financial rating
        if len(fin_tags) >= 1:
            charity['cn_financial'] = float(fin_tags[0].parent.nextSibling.nextSibling.text)
        else:
            print "No Financial cells"
            charity['cn_financial'] = -1.
        # include accountability rating
        if len(acct_tags) >= 1:
            charity['cn_acct_transp'] = float(acct_tags[0].parent.nextSibling.nextSibling.text)
        else:
            print "No Accountability & Transparency cells"
            charity['cn_acct_transp'] = -1.
         
        # compensation of leaders
        compensation = []
        for heading in charsoup.select('h2'):
            comphead = re.findall('Compensation of Leaders', heading.text)
            if len(comphead) > 0:
                comptable = heading.nextSibling.nextSibling
                
                for row in comptable.findAll("tr"):
                    for cell in row.findAll("td"):
                        if re.findall("\$", cell.text):
                            compensation.append(cell.text.strip())
        charity['leader_compensation'] = '+'.join(compensation)
        
        # basic financial info
        expenses = charsoup.find('a', onmouseover=re.compile('Total Functional Expenses')).findNext('td').text
        contributions = charsoup.find('strong', text=re.compile('Total Contributions')).findNext('td').text
        revenue = charsoup.find('strong', text=re.compile('TOTAL REVENUE')).findNext('td').text

        charity['total_expenses'] = int(expenses.strip('$').replace(',', ''))
        charity['total_contributions'] = int(contributions.strip('$').replace(',', ''))
        charity['total_revenue'] = int(revenue.strip('$').replace(',', ''))
        
        metrics = charsoup.find(text=re.compile('Financial Performance Metrics'))
        program = metrics.findNext('a', onmouseover=re.compile('Program Expenses')).findNext('td').text
        administrative = metrics.findNext('a', onmouseover=re.compile('Administrative Expenses')).findNext('td').text
        fundraising = metrics.findNext('a', onmouseover=re.compile('Fundraising Expenses')).findNext('td').text
        
        charity['percent_program'] = float(program.strip('%'))
        charity['percent_admin'] = float(administrative.strip('%'))
        charity['percent_fund'] = float(fundraising.strip('%'))         # compensation of leaders
        compensation = []
        for heading in charsoup.select('h2'):
            comphead = re.findall('Compensation of Leaders', heading.text)
            if len(comphead) > 0:
                comptable = heading.nextSibling.nextSibling
                
                for row in comptable.findAll("tr"):
                    for cell in row.findAll("td"):
                        if re.findall("\$", cell.text):
                            compensation.append(cell.text.strip())
        charity['leader_compensation'] = '+'.join(compensation)
        
        # basic financial info
        expenses = charsoup.find('a', onmouseover=re.compile('Total Functional Expenses')).findNext('td').text
        contributions = charsoup.find('strong', text=re.compile('Total Contributions')).findNext('td').text
        revenue = charsoup.find('strong', text=re.compile('TOTAL REVENUE')).findNext('td').text

        charity['total_expenses'] = int(expenses.strip('$').replace(',', ''))
        charity['total_contributions'] = int(contributions.strip('$').replace(',', ''))
        charity['total_revenue'] = int(revenue.strip('$').replace(',', ''))
        
        metrics = charsoup.find(text=re.compile('Financial Performance Metrics'))
        program = metrics.findNext('a', onmouseover=re.compile('Program Expenses')).findNext('td').text
        administrative = metrics.findNext('a', onmouseover=re.compile('Administrative Expenses')).findNext('td').text
        fundraising = metrics.findNext('a', onmouseover=re.compile('Fundraising Expenses')).findNext('td').text
        
        charity['percent_program'] = float(program.strip('%'))
        charity['percent_admin'] = float(administrative.strip('%'))
        charity['percent_fund'] = float(fundraising.strip('%'))         
        
        # compensation of leaders
        compensation = []
        for heading in charsoup.select('h2'):
            comphead = re.findall('Compensation of Leaders', heading.text)
            if len(comphead) > 0:
                comptable = heading.nextSibling.nextSibling
                
                for row in comptable.findAll("tr"):
                    for cell in row.findAll("td"):
                        if re.findall("\$", cell.text):
                            compensation.append(cell.text.strip())
        charity['leader_compensation'] = '+'.join(compensation)
        
        # basic financial info
        expenses = charsoup.find('a', onmouseover=re.compile('Total Functional Expenses')).findNext('td').text
        contributions = charsoup.find('strong', text=re.compile('Total Contributions')).findNext('td').text
        revenue = charsoup.find('strong', text=re.compile('TOTAL REVENUE')).findNext('td').text

        charity['total_expenses'] = int(expenses.strip('$').replace(',', ''))
        charity['total_contributions'] = int(contributions.strip('$').replace(',', ''))
        charity['total_revenue'] = int(revenue.strip('$').replace(',', ''))
        
        metrics = charsoup.find(text=re.compile('Financial Performance Metrics'))
        program = metrics.findNext('a', onmouseover=re.compile('Program Expenses')).findNext('td').text
        administrative = metrics.findNext('a', onmouseover=re.compile('Administrative Expenses')).findNext('td').text
        fundraising = metrics.findNext('a', onmouseover=re.compile('Fundraising Expenses')).findNext('td').text
        
        charity['percent_program'] = float(program.strip('%'))
        charity['percent_admin'] = float(administrative.strip('%'))
        charity['percent_fund'] = float(fundraising.strip('%'))

        # EIN
        a = charsoup.findAll('a', text='EIN')
        if len(a) > 0:
            ein = re.findall('([0-9]+-*[0-9]*)', a[0].nextSibling)
            if len(ein) > 0:
                charity['ein'] = ein[0]
        
    return dictlist

def clean_features(pandadf):
    # Get organization age
    pandadf['age'] = 2015 - pandadf['year_incorporated']
    pandadf['year_incorporated'][pandadf['year_incorporated'] == 0] = -1
    pandadf['age'][pandadf['year_incorporated'] == -1] = -1

    # Get state
    def extract_state(city_unicode):
        match = re.search(', ([A-Z][A-Z]) [0-9]+', city_unicode)
        if match:
            return match.group(1)
        else:
            return ''
    pandadf['state'] = pandadf['city'].apply(extract_state)

    # Convert tax-exempt status to 0/1
    pandadf['tax_exempt'] = pandadf['tax_status'].apply(lambda x: int(x.find('is tax-exempt under section 501(c)(3)') > -1))
    pandadf[:10][['tax_exempt','tax_status']]

    # Convert CN rating to 0/1
    pandadf['cn_rated'] = pandadf['cn_rated'].apply(lambda x: int(x == u'Rated'))

    # Convert BBB accreditation to 0/1
    pandadf['bbb_accred'] = pandadf['bbb_accred'].apply(lambda x: int(x == u'\nAccredited: Yes\n' or x == u'Accredited Charity'))
    
    return pandadf

# make sure to do sudo mysqld_safe from command line first
def convert_to_sql(pandadf,disease):
    mysqlauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/mysql_user.csv')
    user = mysqlauth.username[0]
    password = mysqlauth.password[0]

    con = mdb.connect('localhost', user, password, 'charity_data')
    # try adding charset='utf8'
    
    table_name = '_'.join(disease.split())
    print "\nTotal records in " + table_name + ": " + str(len(pandadf)) + "\n"
    
    with con:
        cur = con.cursor()
        
        # set up table
        cur.execute("DROP TABLE IF EXISTS " + str(table_name))
        cur.execute("\
            CREATE TABLE " + str(table_name) + "(\
                id INT PRIMARY KEY AUTO_INCREMENT,\
                disease VARCHAR(255),\
                name VARCHAR(255),\
                address VARCHAR(255),\
                city VARCHAR(255),\
                state CHAR(2),\
                ein VARCHAR(20),\
                link VARCHAR(255),\
                donate_link VARCHAR(255),\
                bbb_link VARCHAR(255),\
                facebook_link VARCHAR(255),\
                twitter_link VARCHAR(255),\
                cn_link VARCHAR(255),\
                bbb_accred BOOLEAN,\
                year_incorporated INT,\
                age INT,\
                purpose VARCHAR(255),\
                board_size INT,\
                staff_size INT,\
                tax_status VARCHAR(255),\
                tax_exempt BOOLEAN,\
                cn_rated BOOLEAN,\
                cn_overall FLOAT(8,4),\
                cn_financial FLOAT(8,4),\
                cn_acct_transp FLOAT(8,4),\
                leader_compensation VARCHAR(255),\
                total_expenses INT,\
                total_contributions INT,\
                total_revenue INT,\
                percent_program FLOAT(6,2),\
                percent_admin FLOAT(6,2),\
                percent_fund FLOAT(6,2),\
                facebook_likes INT,\
                twitter_followers INT\
            )"\
        ) 
    
        facebook_likes_placeholder = -1 # not scraped yet

        for idx in range(len(pandadf)):
            try:
                value_str = ("\"" + str(pandadf.name[idx]) + "\",\"" 
                         + str(pandadf.disease[idx]) + "\",\"" 
                         + str(pandadf.address[idx]) + "\",\"" 
                         + str(pandadf.city[idx]) + "\",\"" 
                         + str(pandadf.state[idx]) + "\",\"" 
                         + str(pandadf.ein[idx]) + "\",\"" 
                         + str(pandadf.link[idx]) + "\",\"" 
                         + str(pandadf.donate_link[idx]) + "\",\"" 
                         + str(pandadf.bbb_link[idx]) + "\",\"" 
                         + str(pandadf.facebook_link[idx]) + "\",\"" 
                         + str(pandadf.twitter_link[idx]) + "\",\"" 
                         + str(pandadf.cn_link[idx]) + "\",\"" 
                         + str(pandadf.bbb_accred[idx]) + "\",\"" 
                         + str(pandadf.year_incorporated[idx]) + "\",\"" 
                         + str(pandadf.age[idx]) + "\",\"" 
                         + str(pandadf.purpose[idx]) + "\",\"" 
                         + str(pandadf.board_size[idx]) + "\",\"" 
                         + str(pandadf.staff_size[idx]) + "\",\"" 
                         + str(pandadf.tax_status[idx]) + "\",\"" 
                         + str(pandadf.tax_exempt[idx]) + "\",\"" 
                         + str(pandadf.cn_rated[idx]) + "\",\"" 
                         + str(pandadf.cn_overall[idx]) + "\",\"" 
                         + str(pandadf.cn_financial[idx]) + "\",\"" 
                         + str(pandadf.cn_acct_transp[idx])  + "\",\"" 
                         + str(pandadf.leader_compensation[idx]) + "\",\"" 
                         + str(pandadf.total_expenses[idx]) + "\",\"" 
                         + str(pandadf.total_contributions[idx]) + "\",\"" 
                         + str(pandadf.total_revenue[idx]) + "\",\"" 
                         + str(pandadf.percent_program[idx]) + "\",\"" 
                         + str(pandadf.percent_admin[idx]) + "\",\"" 
                         + str(pandadf.percent_fund[idx]) + "\",\"" 
                         + str(facebook_likes_placeholder) + "\",\"" 
                         + str(pandadf.twitter_followers[idx]) + "\"")
                cur.execute("INSERT INTO " + str(table_name) + "(name, disease, address, city, state, ein, link, \
                         donate_link, bbb_link, facebook_link, twitter_link, cn_link, bbb_accred, \
                         year_incorporated, age, purpose, board_size, staff_size, tax_status, \
                         tax_exempt, cn_rated, cn_overall, cn_financial, cn_acct_transp, \
                         leader_compensation, total_expenses, \
                         total_contributions, total_revenue, percent_program, percent_admin, percent_fund, \
                         facebook_likes, twitter_followers) \
                         VALUES(" + value_str + ")")

            except:
                print pandadf.purpose[idx]
                print "\nProblem converting " + str(idx) + " to SQL."
                print sys.exc_info()
                continue
                
        cur.execute("SELECT * FROM " + str(table_name))
        rows = cur.fetchall()
        #for row in rows:
            #print row

    return rows



# Define main() function to go through diseases and pull charity info.
def main():
    # Cycle through diseases
    disease_list = master_disease_list.return_diseases()

    for disease in disease_list:
        clean_disease_name = ' '.join(disease.lower().replace('\'s disease','').split())
        print "\nProcessing data for " + clean_disease_name + "...\n"
        # TO DO: allow synonymous names (e.g. colon vs colorectal cancer)
        
        # Scrape data
        bbb_soups = scrape_bbb_urls(clean_disease_name)
        bbb_charities = clean_bbb_info(bbb_soups,clean_disease_name)
        charities_with_links = get_charity_links(bbb_charities)
        charities_with_social = scrape_social_media(charities_with_links)
        char_with_twitter = get_twitter_followers(charities_with_social)
        char_with_nav_link = get_char_nav_info(char_with_twitter)
        
        # Convert to Pandas and then to SQl
        panda_char = pd.DataFrame(char_with_nav_link)
        if len(panda_char) > 0:
            panda_clean = clean_features(panda_char)
            sqlrows = convert_to_sql(panda_clean,clean_disease_name)
            
            # Print message to check that code is working and summarize data
            print "\nCharities focused on " + clean_disease_name + ": " + str(len(sqlrows)) + "\n"
    print "Done."


# Boilerplate to call main()
if __name__ == '__main__':
    main()
