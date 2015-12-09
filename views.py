from flask import render_template, request, Flask
#from app import app
import pymysql as mdb
import pandas as pd
import sys, re
import program_rankings as rank
import numpy as np
import copy

app = Flask(__name__)

@app.route('/contact')
def contact():
    """Page with contact information."""
    return render_template("contact.html")

@app.route('/')
@app.route('/index')
@app.route('/input')
@app.route('/insight')
@app.route('/charitychooser')
def input():
    """Input page with options to select charity features."""
    return render_template("input.html")

@app.route('/output')
def output():
    """Find and print charities that match the user's preferences."""

    # Retrieve the desired disease.
    disease = request.args.get('disease')
    clean_disease_name = '_'.join(disease.lower().replace('\'s disease','').replace('\'s','').split())
    the_focus = disease.lower()

    # Store a list of preferences to plug into the SQL query.
    req_list = []

    # Retrieve requested state if any.
    req_state = request.args.get('state')
    if req_state != '':
        req_list.append('state = "' + str(req_state) + '"') 
    
    # Extract other input and store preferences.
    tax_pref = request.args.get('tax_exempt')
    bbb_pref = request.args.get('bbb_accred')
    cn_pref = request.args.get('cn_rated')
    age_pref = request.args.get('age')
    if age_pref != '0':
        req_list.append('age > -1')
    staff_pref = request.args.get('staff_size')
    if staff_pref != '0':
        req_list.append('staff_size > -1')
    board_pref = request.args.get('board_size')
    if board_pref != '0':
        req_list.append('board_size > -1')
    cont_pref = request.args.get('total_contributions')
    if cont_pref != '0':
        req_list.append('total_contributions > -1')
    expense_pref = request.args.get('total_expenses')
    if expense_pref != '0':
        req_list.append('total_expenses > -1')
    program_pref = request.args.get('percent_program')
    if program_pref != '0':
        req_list.append('percent_program > -1')
    twitter_pref = request.args.get('twitter_followers')
    if twitter_pref != '0':
        req_list.append('twitter_followers > -1')
    
    # Convert input to dictionary of user preferences 
    pref_list = {'bbb_accred' : bbb_pref, 
                              'cn_rated' : cn_pref, 
                              'tax_exempt' : tax_pref,
                              'cn_overall' : '3',
                              'cn_acct_transp' : '3', 
                              'cn_financial' : '3', 
                              'percent_program' : program_pref, 
                              'staff_size' : staff_pref, 
                              'board_size' : board_pref,
                              'age' : age_pref, 
                              'total_contributions' : cont_pref, 
                              'total_expenses' : expense_pref,
                              'total_revenue' : cont_pref,
                              'twitter_followers' : twitter_pref }

    # Convert all preferences from string to float.
    for pref in pref_list.viewkeys():
        if pref_list[pref] == '':
            pref_list[pref] = 0.
        else:
            pref_list[pref] = float(pref_list[pref])
            
    # Construct the ideal charity.
    ideal_char = rank.convert_prefs_to_ideal(pref_list)
    
    # Set order of features in the ideal charity.
    feature_names = ['bbb_accred', 'tax_exempt', 'cn_rated', 'cn_overall', 'cn_acct_transp', 'cn_financial', 'percent_admin', 
                     'percent_fund', 'percent_program', 'staff_size', 'board_size',
                     'age', 'total_contributions', 'total_expenses', 'total_revenue', 'twitter_followers']

    ideal_char = ideal_char[feature_names]

    # Make command to read SQL table into pandas data frame and convert to list of dictionaries
    req_string = ' AND '.join(req_list)
    
    # Open connection to MySQL database.
    mysqlauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/mysql_user.csv')
    sqluser = mysqlauth.username[0]
    sqlpass = mysqlauth.password[0]

    con = mdb.connect(user=sqluser, host="localhost", db="charity_data", password=sqlpass, charset='utf8')

    # Pull charities from database.
    # 1. Base case, where user has not specified preferences.
    if req_string == '':
        try:
            with con:
                panda_char = pd.read_sql("SELECT * FROM " + str(clean_disease_name), con)
        except: # User asked for a disease that isn't in the database.
            print sys.exc_info()
            custom_error = "Sorry, that disease is not in our database."
            charities = []
            the_result = 0
            # Specify options for output page to be presented.
            return render_template("output.html", charities = charities, the_result = the_result, the_focus = the_focus, the_input = pref_list, custom_error = custom_error)

    # 2. Expected case, where user has entered preferences.
    else:
        try:
            with con:
                panda_char = pd.read_sql("SELECT * FROM " + str(clean_disease_name) + " WHERE " + str(req_string), con)
        except: # User asked for a disease that isn't in the database.
            print sys.exc_info()
            custom_error = "Sorry, that disease is not in our database." 
            charities = []
            the_result = 0
            # Specify options for output page to be presented.
            return render_template("output.html", charities = charities, the_result = the_result, the_focus = the_focus, the_input = pref_list, custom_error = custom_error)

    # close database
    con.close()
    
    # Get rankings 
    if len(panda_char) == 0: # The disease is in the database, but there are no charities from the desired state or no charities have enough non-missing data.
        custom_error = "Sorry, no organizations meet your criteria. Try removing some of your filters."
        charities = []
        the_result = 0
        # Specify options for output page to be presented.
        return render_template("output.html", charities = charities, the_result = the_result, the_focus = the_focus, the_input = pref_list, custom_error = custom_error)
    else: # If at least one organization was read in, rank them.
        top_charities = rank.rank_programs(panda_char, ideal_char)
        
    the_result = str(0) #placeholder for now - the_result is only used for debugging
  
    """
    In an ideal version, we'd want to return:
    (1) ranked list of charities that meet user's specified preferences ('charities')
    (2) if no programs in (1), ranked list of charities that are don't meet user's preferences ('close_charities')
    (3) alternative suggestions based on different choices
    Which tables to print will be determined in output.html based on what lists are returned.
    """


    # Clean charity data for nice printing.
    charities = top_charities.to_dict(outtype='records')

    for charity in charities:
        # Translate 0/1 to no/yes.
        for key in ['bbb_accred', 'cn_rated', 'tax_exempt']:
            if charity[key] == 1.:
                charity[key] = 'Yes'
            elif charity[key] == 0.:
                charity[key] = 'No'
            else:
                charity[key] = '--'

        # Round floating-point numbers.
        for key in ['cn_overall', 'cn_financial', 'cn_acct_transp']:
            if np.isnan(charity[key]):
                charity[key] = '--'
            else:
                charity[key] = '{:.2f}'.format(charity[key])

        # Round integers and include commas .
        for key in ['twitter_followers', 'board_size', 'staff_size']:
            if np.isnan(charity[key]):
                charity[key] = '--'
            else:
                charity[key] = '{:,.0f}'.format(charity[key])

        # Round integers that shouldn't have commas.
        for key in ['year_incorporated']:
            if np.isnan(charity[key]):
                charity[key] = '--'
            else:
                charity[key] = '{:.0f}'.format(charity[key])

        # Add '%' to percentages.
        for key in ['percent_fund', 'percent_program', 'percent_admin']:
            if np.isnan(charity[key]):
                charity[key] = '--'
            else:
                charity[key] = '{:.1f}%'.format(charity[key])

        # Add '$' to dollar amounts.
        for key in ['total_expenses','total_contributions']:
            if np.isnan(charity[key]):
                charity[key] = '--'
            else:
                charity[key] = '${:,.0f}'.format(charity[key])

    # Specify options for output page to be presented.
    return render_template("output.html", charities = charities, the_result = the_result, the_focus = the_focus, the_input = pref_list, custom_error = '')

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
