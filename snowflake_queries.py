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




def get_snowflake_data(query, columns):

    ctx = snowflake.connector.connect(
    user='NROBERTSON@EDX.ORG', ## removed
    password='Thes9Pian2!1992', ## removed
    account='edx.us-east-1',
    warehouse='POWER_USER_ADHOC_XL',
    database='PROD',
    role='NROBERTSON_ROLE', ## removed
        )

    # Establish Snowflake cursor.
    cur = ctx.cursor()

    def run_query(query, columns):
        cur.execute(query)
        results = cur.fetchall()
        arr = np.array(results)
        df = pd.DataFrame(arr, columns=columns)
        return df

    df = run_query(query=query, columns=columns)
    return df


# Get courses to match with a company / industry.

sql1 = """
SELECT
    tcs.course_key,
    split_part(tcs.course_key,'+',1) as partner,
    cmc.title,
    'https://www.edx.org/course/' || cmc.url_slug as url,
    'https://prod-discovery.edx-cdn.org/' || cmc.image as image_link,
    cmc.enrollment_count,
    LISTAGG(ts.name, ', ') as skills
FROM
    discovery_pii.taxonomy_courseskills as tcs
LEFT JOIN
    discovery_pii.taxonomy_skill as ts
ON
    tcs.skill_id = ts.id
LEFT JOIN
    discovery_pii.course_metadata_course as cmc
ON
    tcs.course_key = cmc.key
WHERE
    tcs.is_blacklisted = FALSE
AND
    cmc.enrollment_count >= 100
AND
    cmc.draft = False
GROUP BY
    1,2,3,4,5,6
ORDER BY
    6 DESC
        """

cols1 = ['course_key','partner','title','url','image_link','enrollment_count', 'skills']


# Get business subscription catalog.

sql2 = """
SELECT
    qtc.course_key
FROM
    enterprise.map_catalog_query_to_content qtc
WHERE
    -- UUID for OC Subscription catalog.
    catalog_query_uuid = 'b90a0c2339ca47acb087a31c4586c08b'
"""

cols2 = ['course_key']

b2b_subs_catalog = get_snowflake_data(query=sql2, columns=cols2)


# Get online campus subscription catalog.

sql3 = """
SELECT
    qtc.course_key
FROM
    enterprise.map_catalog_query_to_content qtc
WHERE
    -- UUID for OC Subscription catalog.
    catalog_query_uuid = '703cfd8977b44aa38f733a9915be3897'
"""

cols3 = ['course_key']

oc_subs_catalog = get_snowflake_data(query=sql3, columns=cols3)



# Get job-skill mappings, ranked by # of unique postings.

sql4 = """
SELECT
    tj.name as job_name,
    tjs.significance,
    tjs.unique_postings,
    ts.name as skill_name
FROM 
    discovery_pii.taxonomy_jobskills as tjs
LEFT JOIN
    discovery_pii.taxonomy_job as tj
ON
    tjs.job_id = tj.id
LEFT JOIN
    discovery_pii.taxonomy_skill as ts
ON
    tjs.skill_id = ts.id
ORDER BY
    tj.name,
    tjs.unique_postings DESC
"""

cols4 = ['job_name','signficance','unique_postings','skill_name']

job_skills_mapping = get_snowflake_data(query=sql4, columns=cols4)
