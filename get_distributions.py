#!/usr/bin/env python

import pymysql as mdb
import pandas as pd
import numpy as np
import re
import MySQLdb
import master_disease_list

mysqlauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/mysql_user.csv')
sqluser = mysqlauth.username[0]
sqlpass = mysqlauth.password[0]

con = mdb.connect(user=sqluser, host="localhost", db="charity_data", password=sqlpass, charset='utf8')

# Set up SQL table with distributions of features for faster conversion of user input.
def main():
    # Set up SQL connection
    mysqlauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/mysql_user.csv')
    sqluser = mysqlauth.username[0]
    sqlpass = mysqlauth.password[0]
    
    con = mdb.connect(user=sqluser, host="localhost", db="charity_data", password=sqlpass, charset='utf8')
    
    # Read in SQL data to get distributions for some variables.
    combined_panda = pd.DataFrame(dtype=float)
    disease_list = master_disease_list.return_diseases()

    with con:
        for disease in disease_list:
            clean_disease_name = '_'.join(disease.lower().replace('\'s disease','').replace('\'s','').split())
            pandadf = pd.read_sql("SELECT cn_overall, cn_financial, cn_acct_transp, year_incorporated, age, twitter_followers, \
                percent_admin, percent_fund, percent_program, \
                total_contributions, total_expenses, total_revenue, staff_size, board_size FROM " + str(clean_disease_name), con)
            if len(pandadf) > 0:
                combined_panda = pd.concat([combined_panda, pandadf], 0, ignore_index=True)

    # Fix NaNs that were originally encoded as -1.
    for idx in range(len(combined_panda)):
        if combined_panda['year_incorporated'][idx] == -1.:
            combined_panda[idx:(idx+1)]['age'] = np.nan
            combined_panda[idx:(idx+1)]['year_incorporated'] = np.nan
        for col in combined_panda.columns:
            if combined_panda[col][idx] == -1:
                combined_panda[idx:(idx+1)][col] = np.nan

    # Make data frame with distributions of each feature.
    distribution = pd.DataFrame(columns=combined_panda.columns, index=['p0','p17','p25','p50','p75','p83','p100'], dtype='float')

    for col in distribution.columns:
        quantiles = combined_panda[col].describe(percentile_width=50.)
        distribution.loc['p0',col] = quantiles['min']
        distribution.loc['p25',col] = quantiles['25%']
        distribution.loc['p50',col] = quantiles['50%']
        distribution.loc['p75',col] = quantiles['75%']
        distribution.loc['p100',col] = quantiles['max']
        
        quantiles = combined_panda[col].describe(percentile_width=66.7)
        distribution.loc['p17',col] = quantiles['16.6%']
        distribution.loc['p83',col] = quantiles['83.4%']
    distribution['distidx'] = distribution.index 

    # Save distribution table
    db = MySQLdb.connect(read_default_file='/home/kristy/Documents/auth_codes/my.cnf')
    db.query("CREATE DATABASE IF NOT EXISTS charity_data;")
    db.query("USE charity_data;")
    db.query("DROP TABLE IF EXISTS distribution;")
    distribution.to_sql(name = 'distribution', con = db, flavor = 'mysql')
    db.close() 


# Boilerplate to call main()
if __name__ == '__main__':
    main()

