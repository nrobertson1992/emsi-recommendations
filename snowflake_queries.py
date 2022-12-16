# For calling the API and manipulating data.
import requests
import numpy as np
import pandas as pd
import json

# What you need for running streamlit!
import streamlit as st

# Miscellaneous packages.
from datetime import datetime
import snowflake.connector



# Returns a dataframe of data from edX's Snowflake. You need to find a way
# store passwords better than this, even for a private GitHub Repo.
def get_snowflake_data(query, columns):

    # Creation the connection.
    ctx = snowflake.connector.connect(
    user=st.secrets['DB_USERNAME'],
    password=st.secrets['DB_TOKEN'],
    account=st.secrets['info']['account'],
    warehouse=st.secrets['info']['warehouse'],
    database=st.secrets['info']['database'],
    role=st.secrets['info']['role'],
        )


    # Establish Snowflake cursor.
    cur = ctx.cursor()

    # Run the query.
    def run_query(query, columns):
        cur.execute(query)
        results = cur.fetchall()
        arr = np.array(results)
        df = pd.DataFrame(arr, columns=columns)
        return df

    df = run_query(query=query, columns=columns)

    # Return the dataframe.
    return df


# Get courses to match with a company / industry.

sql1 = st.secrets['info']['sql1']

cols1 = ['course_key','partner','title','short_description','url','image_link','enrollment_count', 'skills']


# Get business subscription catalog.

sql2 = st.secrets['info']['sql2']

cols2 = ['course_key']

b2b_subs_catalog = get_snowflake_data(query=sql2, columns=cols2)


# Get online campus subscription catalog.

sql3 = st.secrets['info']['sql3']

cols3 = ['course_key']

oc_subs_catalog = get_snowflake_data(query=sql3, columns=cols3)



# Get job-skill mappings, ranked by # of unique postings.

sql4 = st.secrets['info']['sql4']

cols4 = ['job_name','signficance','unique_postings','skill_name']

job_skills_mapping = get_snowflake_data(query=sql4, columns=cols4)
