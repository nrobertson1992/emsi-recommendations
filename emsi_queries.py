# For calling the API and manipulating data.
import requests
import numpy as np
import pandas as pd
import json

# What you need for running streamlit!
import streamlit as st

# Miscellaneous packages.
from datetime import datetime


# Define here your dictionary of NAICS 2. Each NAICS name maps to one or more naics codes.
# For consistency, I'm storing all of the codes as lists, even if there is only one -- it allows me
# to handle the values in this dictionary consistently. In the future, I'd imagine building this out
# to support NAICS3, 4, 5, and 6 for more targeted values.
naics2_dictionary = {
         'Agriculture, Forest, Fishing and Hunting': ['11'],
         'Mining': ['21'], 
         'Utilities': ['22'], 
         'Construction': ['23'], 
         'Manufacturing': ['31','32','33'],
         'Wholesale Trade': ['42'], 
         'Retail Trade': ['44','45'], 
         'Transportation and Warehousing': ['48','49'],
         'Information': ['51'], 
         'Finance and Insurance': ['52'], 
         'Real Estate and Rental and Leasing': ['53'],
         'Professional, Scientific, and Technical Services': ['54'], 
         'Management of Companies and Enterprises': ['55'],
         'Administrative and Support and Waste Management and Redmediation Services': ['56'],
         'Educational Services': ['61'],
         'Health Care and Social Assistance': ['62'],
         'Arts, Entertainment, and Recreation': ['71'],
         'Accommodation and Food Services': ['72'],
         'Other Services (except Public Administration)': ['81'],
         'Public Administration': ['92'] }




# Get the token. In the future, consider if there is a better way to handle hosting thiss
# client secret on github.
def get_token(scope, client_id='edx',client_secret='bf4e64b4abb44b0abec812f9a9e6f58c'): 
    
    # Connecting to API for OAuth2 token.
    # Setting up payload with id, secret, and scope.
    # Request "POST" response using the url.
    # Extract the token.
    
    url = "https://auth.emsicloud.com/connect/token"
    payload = "client_id={}&client_secret={}&grant_type=client_credentials&scope={}".format(client_id,client_secret,scope)
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, data=payload, headers=headers)
    token = response.json()['access_token']
    return token

# Get the dataframe.
def get_top_skills(start_date, end_date, company_name, sort, search_type, industry_name):

    # Call JPA (Jobs Postings API).
    headers = {'Authorization': 'Bearer {}'.format(get_token(scope='postings:us')), 'content-type': 'application/json'}
    
    # Get the top 10 skills for the company.
    if search_type == 'By Company':
        url = 'https://emsiservices.com/jpa/rankings/company_name/rankings/skills_name'

        payload = """{
          "filter": {
            "when": {
              "start": \"""" + start_date + """\",
              "end": \"""" + end_date + """\",
              "type": "active"
                },
            "company_name": {
                "include": [
                 \"""" + company_name + """\" 
                ],
                "include_op": "or"
                  }
            },
          "rank": {
            "by": "unique_postings",
            "limit": 100
          },
          "nested_rank": {
            "by": \"""" + sort + """\" ,
            "limit": 10
          }
            }"""

    # Get the top 10 skills for the industry. This is limited to NAICS 2. In the future,
    # You'll need to change how the industry_name works. Perhaps one large dictionary?
    # Or one dictionary for each NAICS level so you can separate them by filtering?
    elif search_type == 'By Industry':
        url = 'https://emsiservices.com/jpa/rankings/naics2_name/rankings/skills_name'
        
        industry_name = naics2_dictionary[industry_name]
        industry_string = ''

        for industry in industry_name:
            industry_string += '"' + str(industry) + '",'

        industry_string = industry_string[:-1]

        payload = """{
          "filter": {
            "when": {
              "start": \"""" + start_date + """\",
              "end": \"""" + end_date + """\",
              "type": "active"
                },
                "naics2": [
                 """ + industry_string + """ 
                ]
            },
          "rank": {
            "by": "unique_postings",
            "limit": 100
          },
          "nested_rank": {
            "by": \"""" + sort + """\" ,
            "limit": 10
          }
            }"""  


    
    # Call the API using the payload. 
    r = requests.request("POST", url, data=payload, headers=headers)    
    r = json.loads(r.text)
    company_skills = r['data']['ranking']['buckets']

    
    ## Create lists for capturing the values.
    cs_company_list = []
    cs_skill_list = []
    cs_significance_list = []
    cs_unique_postings_list = []
    
    # For company within massive company blob.
    for company in company_skills:
        
        # For skill nested within each cmopany.
        for skill in company['ranking']['buckets']:
            cs_company = company["name"]
            cs_company_list.append(cs_company)
    
            cs_skill = skill['name']
            cs_skill_list.append(cs_skill)
    		    
            # If significance is how it is being sorted, extract significance.
            if sort == 'significance':
            	cs_significance = skill['significance']
            	cs_significance_list.append(cs_significance)
        
            cs_unique_postings = skill['unique_postings']
            cs_unique_postings_list.append(cs_unique_postings)

    # Create df for company-skill demand.
    company_skills_df = pd.DataFrame()

    # Write data to df.
    company_skills_df['company'] = cs_company_list
    company_skills_df['skills'] = cs_skill_list

    # If significance is how it is being sorted, created column for significance.
    if sort == 'significance':
        company_skills_df['significance'] = cs_significance_list

    company_skills_df['unique_postings'] = cs_unique_postings_list
        
    return company_skills_df    


# Get the dataframe.
def get_top_jobs(start_date, end_date, company_name, sort, search_type, industry_name):

    # Call JPA (Jobs Postings API).
    headers = {'Authorization': 'Bearer {}'.format(get_token(scope='postings:us')), 'content-type': 'application/json'}
    
    # Get the top 10 jobs for the company.
    if search_type == 'By Company':
        url = 'https://emsiservices.com/jpa/rankings/company_name/rankings/title_name'
    # Default max limit is 10. Have to 
    # reach out to Emsi to get more than 10.
        payload = """{
          "filter": {
            "when": {
              "start": \"""" + start_date + """\",
              "end": \"""" + end_date + """\",
              "type": "active"
                },
            "company_name": {
                "include": [
                 \"""" + company_name + """\" 
                ],
                "include_op": "or"
                  }
            },
          "rank": {
            "by": "unique_postings",
            "limit": 100
          },
          "nested_rank": {
            "by": \"""" + sort + """\" ,
            "limit": 10
          }
            }"""


    # Get the top 10 jobs for the industry. This is limited to NAICS 2. In the future,
    # You'll need to change how the industry_name works. Perhaps one large dictionary?
    # Or one dictionary for each NAICS level so you can separate them by filtering?
    elif search_type == 'By Industry':
        url = 'https://emsiservices.com/jpa/rankings/naics2_name/rankings/title_name'

        industry_string = ''

        industry_name = naics2_dictionary[industry_name]
        for industry in industry_name:
            industry_string += '"' + str(industry) + '",'

        industry_string = industry_string[:-1]


        payload = """{
          "filter": {
            "when": {
              "start": \"""" + start_date + """\",
              "end": \"""" + end_date + """\",
              "type": "active"
                },
                "naics2": [
                 """ + industry_string + """ 
                ]
            },
          "rank": {
            "by": "unique_postings",
            "limit": 100
          },
          "nested_rank": {
            "by": \"""" + sort + """\" ,
            "limit": 10
          }
            }"""        
    
    # Call the API using the payload. 
    r = requests.request("POST", url, data=payload, headers=headers)    
    r = json.loads(r.text)
    company_jobs = r['data']['ranking']['buckets']

    
    ## Create lists for capturing the values.
    cs_company_list = []
    cs_job_list = []
    cs_significance_list = []
    cs_unique_postings_list = []
    
    # For company within massive company blob.
    for company in company_jobs:
        
        # For skill nested within each cmopany.
        for job in company['ranking']['buckets']:
            cs_company = company["name"]
            cs_company_list.append(cs_company)
    
            cs_job = job['name']
            cs_job_list.append(cs_job)
            
            # If sorting by signficiance, extract that.
            if sort == 'significance':
                cs_significance = job['significance']
                cs_significance_list.append(cs_significance)
        
            cs_unique_postings = job['unique_postings']
            cs_unique_postings_list.append(cs_unique_postings)

    # Create df for company-skill demand.
    company_jobs_df = pd.DataFrame()

    # Write data to df.
    company_jobs_df['company'] = cs_company_list
    company_jobs_df['jobs'] = cs_job_list

    # If extracting signficance, add a column for that.
    if sort == 'significance':
        company_jobs_df['significance'] = cs_significance_list
    company_jobs_df['unique_postings'] = cs_unique_postings_list
        
    return company_jobs_df


# This is used to handle the error case when someone searches a company that is now
# found in the Emsi API. Instead, we return a list of possible search values to help
# people see the company that are the closest in value to what was searched. This helps
# Them populate the correct value for a search term.
def company_query(term):
    
    url = "https://emsiservices.com/jpa/taxonomies/company"
    
    querystring = {"q": term}
    
    headers = {'Authorization': 'Bearer {}'.format(get_token(scope='postings:us')), 'content-type': 'application/json'}
    r = requests.request("GET", url, params=querystring, headers=headers)
    
    r = json.loads(r.text)
    companies = r['data']
        
    company_string = ''
    for company in companies:
        company_string += company['name']
        company_string += ', '
    company_string = company_string[:-2] + '.'

    return company_string