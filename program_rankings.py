import pandas as pd
import numpy as np
import pymysql as mdb

def convert_prefs_to_ideal(pref_list):
    """"Convert user preferences to the same format as organizations in the database. """

    # Construct initial dataframe.
    ideal_df = pd.DataFrame(columns=pref_list.viewkeys(), index=[1000], dtype='float64')

    # Set up MySQL connection.
    mysqlauth = pd.DataFrame.from_csv('/home/kristy/Documents/auth_codes/mysql_user.csv')
    sqluser = mysqlauth.username[0]
    sqlpass = mysqlauth.password[0]
    
    con = mdb.connect(user=sqluser, host="localhost", db="charity_data", password=sqlpass, charset='utf8')

    # Read in distributions from SQL database.
    with con:
        distribution = pd.read_sql("SELECT * FROM distribution", con)
    distribution.index = distribution.distidx    

    # Close MySQL connection
    con.close()

    # Booleans are just scored as important or not.
    for col in ['bbb_accred', 'cn_rated', 'tax_exempt']:
        if pref_list[col] == 0: # no preference
            ideal_df[:][col] = np.nan
        elif pref_list[col] == 1: # prefer 'yes'
            ideal_df[:][col] = 1.
        elif pref_list[col] == 2: # prefer 'no'
            ideal_df[:][col] = 0.
        else:
            raise Exception('Improper input for ' + str(col) + ': ' + str(pref_list[col]) + ' (' + str(type(pref_list[col])) + ').')

    # Numerical values are defined based on the overall distribution.
    for col in ['staff_size','board_size','total_contributions','total_expenses','percent_program','twitter_followers','age','cn_overall','cn_financial','cn_acct_transp','total_revenue']:
        if pref_list[col] == 0: # no preference
            ideal_df[:][col] = np.nan
        elif  pref_list[col] == 1: # prefer 'low'
            ideal_df[:][col] = distribution.loc['p0',col]
        elif pref_list[col] == 2: # prefer 'middle'
            ideal_df[:][col] = distribution.loc['p50',col]
        elif pref_list[col] == 3: # prefer 'high'
            ideal_df[:][col] = distribution.loc['p100',col]
        else:
            raise Exception('Improper input for ' + str(col) + ': ' + str(pref_list[col]) + ' (' + str(type(pref_list[col])) + ').')

    # At least for now, some values are hardcoded here
    for col in ['percent_admin','percent_fund']:
        ideal_df[col] = (100. - ideal_df['percent_program']) / 2.

    return ideal_df

def clean_data(data_df):
    """Clean up data after transfering through SQL."""

    # Change integers to floats so that NaNs work
    for col in data_df.columns:
        if data_df[col].dtype == 'int':
            data_df[col] = data_df[col].astype('float')
    data_df.dtypes # Without this line, the conversion doesn't work. I have no idea why.

    # Clean up missing values.
    for idx in range(len(data_df)):
        if data_df['cn_rated'][idx] <= 0: # No Charity Navigator features is charity wasn't rated.
            for col in ['cn_overall', 'cn_acct_transp', 'cn_financial', 'percent_admin', 'percent_fund', 'percent_program', 
                        'total_contributions', 'total_expenses', 'total_revenue']:
                data_df.ix[idx:(idx+1),col] = np.nan

        if data_df['year_incorporated'][idx] == -1: # No age if year is missing.
            data_df.ix[idx:(idx+1),'age'] = np.nan
            data_df.ix[idx:(idx+1),'year_incorporated'] = np.nan
        for col in data_df.columns: # Missing values were encoded as -1 in SQL. We want them to be NaN now.
            if data_df[col][idx] == -1:
                data_df.ix[idx:(idx+1),col] = np.NaN

    return data_df


def gower_similarity(data_df,ref_df):
    """Define Gower similarity metric for a single row."""

    # Set up data structures
    feature_names = ref_df.columns
    nFeatures = len(feature_names)
    sim = np.empty([nFeatures,1]) # each feature's similarity index (in [0, 1])
    wgt = np.empty([nFeatures,1]) # weight to put on each feature (0 or 1)

    # Find similarity for each feature
    # 'any' is only used for correct syntax -- each comparison is on a single number
    # 'np.sum' is used to convert series with a single number into scalar
    for idx in range(len(feature_names)):
        col = feature_names[idx]
        if ref_df[col].dtype == 'bool': # Jaccard similarity for booleans.
            sim[idx] = any(ref_df[col] == 1) and data_df[col] == 1
            wgt[idx] = any(ref_df[col] == 1) or data_df[col] == 1

        elif ref_df[col].dtype in ['float', 'int']: # Manhattan distance for numbers.
            sim[idx] = 1 - np.absolute(np.sum(ref_df[col]) - np.sum(data_df[col]))
            wgt[idx] = any(np.isfinite(ref_df[col])) and np.isfinite(data_df[col])
        else:
            print "Error: {} is not boolean or numeric.".format(col)
            
    # Find and return weighted average as overall similarity.
    return np.nansum(sim) / np.nansum(wgt)

def rank_programs(fulldf = pd.DataFrame(np.empty([0,0])), ideal_org = pd.DataFrame(np.empty([0,0]))):
    """
    Rank programs based on criteria specified by user.
    Assume ideal_org consists of only the features of interest.
    """

    # If there are no programs to rank, don't do anything.
    if fulldf.empty:
        return fulldf

    # Clean up missing data
    fulldf = clean_data(fulldf)

    # Set parameters
    max_output = 10 # number of organizations to print
    feature_names = ideal_org.columns

    # Make simpler dataframe with only the relevant fields
    reduceddf = fulldf[:][feature_names]

    # Normalize values
    for col in feature_names:
        minval = np.min([np.min(ideal_org[col]), np.min(reduceddf[col])])
        ideal_org[col] -= minval
        reduceddf[col] -= minval
        maxval = np.max([np.max(ideal_org[col]), np.max(reduceddf[col])])
        ideal_org[col] /= maxval
        reduceddf[col] /= maxval

    # Find Gower similarity for each organization.
    dists = pd.Series(index=reduceddf.index, name='gower')
    for idx, r in reduceddf.iterrows():
        dists[idx] = gower_similarity(r, ideal_org)

    # Merge similarity scores with other data
    fulldf['gower'] = dists   
    
    # Rank charities based on distance metric.
    fulldf.gower.fillna(value=-1, inplace=True) # convert missing to -1 for easier sorting
    fulldf.sort(columns='gower', ascending=False, inplace=True)
    fulldf['ranking'] = range(1,len(fulldf)+1)
    top_charities = fulldf[:max_output]

    return top_charities


