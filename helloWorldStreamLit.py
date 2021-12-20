# Use what you learned in mortgage.py to make magic happen.

# For calling the API and manipulating data.
import requests
import numpy as np
import pandas as pd
import json

# For making beautiful visuals.
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
sns.set_color_codes('muted')

# What you need for running streamlit!
import streamlit as st
from annotated_text import annotated_text

# For Emsi and Snowflake data extraction! Custom built.
import emsi_queries as eq
import snowflake_queries as sq

# Miscellaneous packages.
from datetime import datetime
from PIL import Image
from io import BytesIO
import inflect
p = inflect.engine()
import datetime as dt

# Set page title and main page.
st.set_page_config(page_title="Labor Market Research Tool")
st.title("Labor Market Research Tool")

st.write("This is an internal tool, designed first for marketing, to help them find top skills and jobs in certain industries and companies, as well as courses those industries and companies might be interested in. The goal is to use this information to drive activities such as: A/B language tests on LinkedIn Campaigns, targeted Account-Based Marketing outreach, enable experiments of matching content to prospects based on the skill trends at their organization.")


# Add input values for each header.
st.sidebar.subheader('Details')

search = st.sidebar.radio(
     "How would like to search?",
     ('By Company', 'By Industry'))

if search == 'By Company':
     company_name = st.sidebar.text_input("Enter the company you are searching for:", "IBM")
     industry_name = ''

elif search == 'By Industry':
     naics_level = st.sidebar.selectbox("What level of NAICS industry are you searching? (only 2 supported)", ("2"))
     if naics_level == "2":
         ## TODO: create a naics 2 dictionary, turn the keys into a tuple, feed that through the NAICS.

         industry_name = st.sidebar.selectbox("Enter the NAICS industry you are searching for:", tuple(eq.naics2_dictionary.keys()))
         company_name = ''


#company_name = st.sidebar.text_input("Enter the company you are searching for:", "Microsoft")
metric = st.sidebar.selectbox("Do you want to search for top job or skill?", ("Skills","Jobs"))
sort = st.sidebar.selectbox('Rank results by:', ('Unique Postings', 'Significance'))
start_date = st.sidebar.date_input("Enter the start date for your query:",value=dt.date(2021,1,1))
end_date = st.sidebar.date_input("Enter the end date for your query:", value=dt.date(2021,12,31))


# Convert start and end dates to correct string formatting.
start_date = start_date.strftime("%Y-%m-%d")
end_date = end_date.strftime("%Y-%m-%d")

# Convert pretty sort value into value Emsi API can understand.
if sort == 'Significance':
	sort = 'significance'
if sort == 'Unique Postings':
	sort = 'unique_postings'

if metric == 'Skills':
    metric = 'skills'
if metric == 'Jobs':
    metric = 'jobs'

# Generate the top skills dataframe.
if metric == "skills":
    emsi_df = eq.get_top_skills(start_date=start_date,end_date=end_date,company_name=company_name, sort=sort, search_type=search, industry_name=industry_name)
if metric == "jobs":
    emsi_df = eq.get_top_jobs(start_date=start_date,end_date=end_date,company_name=company_name, sort=sort, search_type=search, industry_name=industry_name)


if len(emsi_df) > 0:

    # Show top 10 skills.
    st.subheader('Labor Market Analysis')
    st.write('Top 10 {} for {}, ranked by {}, from {} to {}.'.format(metric, company_name + industry_name, sort, start_date, end_date))
    c = alt.Chart(emsi_df).mark_bar().encode(
                x=alt.X(sort), 
                y=alt.Y(metric, sort='-x'),
                tooltip=[sort]
            )
  

    st.altair_chart(c, use_container_width=True)


    courses_df = sq.get_snowflake_data(query=sq.sql1, columns=sq.cols1)
    # Transform the column's data structure to lists.
    def listify(x):
        return list(x.split(', '))

    # Apply the function.
    courses_df['skills'] = courses_df['skills'].apply(listify)

    def intersection_ratio(set_a, set_b):
        intersection = set_a.intersection(set_b)
        intersection_ratio = len(intersection)/len(set_a)
        return intersection_ratio

    def intersection(set_a, set_b):
        intersection = set_a.intersection(set_b)
        return list(intersection)

    def annotations(df, col1, col2, index):
        list_ = []
        for skill in df[col1].iloc[index]:
            if skill in df[col2].iloc[index]:
                list_.append((skill,"","#8ef"))
                list_.append(', ')
            else:
                list_.append(skill)
                list_.append(', ')

        return list_[:-1]

    st.subheader('Top Recommended Courses for {}'.format(company_name + industry_name))




    if metric == 'skills':

        catalog = st.selectbox("Filter by catalog.", ("All edX Courses","Business Subscription","Online Campus Subscription"))

        courses_df['intersection_ratio'] = [intersection_ratio(set_a=set(emsi_df[metric]), set_b=set(set_b)) for set_b in courses_df.skills]
        courses_df['intersection'] = [intersection(set_a=set(emsi_df[metric]), set_b=set(set_b)) for set_b in courses_df.skills]


        if catalog == 'Business Subscription':
            courses_df = courses_df[courses_df.course_key.isin(sq.b2b_subs_catalog.course_key)]
        if catalog == 'Online Campus Subscription':
            courses_df = courses_df[courses_df.course_key.isin(sq.oc_subs_catalog.course_key)]
        courses_df = courses_df.sort_values(by=['intersection_ratio','enrollment_count'], ascending=False)


        col1, col2, col3 = st.columns(3)

        with col1:
            st.write('**Course 1**')
            response = requests.get(courses_df.image_link.iloc[0])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[0]
            url = courses_df.url.iloc[0]
            title = courses_df.title.iloc[0]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=0)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 4**')
            response = requests.get(courses_df.image_link.iloc[3])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[3]
            url = courses_df.url.iloc[3]
            title = courses_df.title.iloc[3]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=3)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 7**')
            response = requests.get(courses_df.image_link.iloc[6])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[6]
            url = courses_df.url.iloc[6]
            title = courses_df.title.iloc[6]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=6)
            annotated_text(
                *annots
                )

        with col2:

            st.write('**Course 2**')
            response = requests.get(courses_df.image_link.iloc[1])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[1]
            url = courses_df.url.iloc[1]
            title = courses_df.title.iloc[1]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=1)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 5**')
            response = requests.get(courses_df.image_link.iloc[4])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[4]
            url = courses_df.url.iloc[4]
            title = courses_df.title.iloc[4]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=4)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 8**')
            response = requests.get(courses_df.image_link.iloc[7])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[7]
            url = courses_df.url.iloc[7]
            title = courses_df.title.iloc[7]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=7)
            annotated_text(
                *annots
                )

        with col3:

            st.write('**Course 3**')
            response = requests.get(courses_df.image_link.iloc[2])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[2]
            url = courses_df.url.iloc[2]
            title = courses_df.title.iloc[2]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=2)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 6**')
            response = requests.get(courses_df.image_link.iloc[5])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[5]
            url = courses_df.url.iloc[5]
            title = courses_df.title.iloc[5]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=5)
            annotated_text(
                *annots
                )

            st.write('')
            st.write('**Course 9**')
            response = requests.get(courses_df.image_link.iloc[8])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[8]
            url = courses_df.url.iloc[8]
            title = courses_df.title.iloc[8]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=8)
            annotated_text(
                *annots
                )

    if metric == 'jobs':



        col1, col2 = st.columns(2)

        with col1:
            catalog = st.selectbox("Filter by catalog.", ("All edX Courses","Business Subscription","Online Campus Subscription"))

        with col2:

            def singularize(x):
                return p.singular_noun(x)
            emsi_df['jobs'] = emsi_df['jobs'].apply(singularize)
            job = st.selectbox("Filter by top job.", (emsi_df.jobs.values))


        job_skills = sq.job_skills_mapping[sq.job_skills_mapping['job_name'] == job][['skill_name']]

        
        if len(job_skills) > 0:

            courses_df['intersection_ratio'] = [intersection_ratio(set_a=set(job_skills['skill_name']), set_b=set(set_b)) for set_b in courses_df.skills]
            courses_df['intersection'] = [intersection(set_a=set(job_skills['skill_name']), set_b=set(set_b)) for set_b in courses_df.skills]


            if catalog == 'Business Subscription':
                courses_df = courses_df[courses_df.course_key.isin(sq.b2b_subs_catalog.course_key)]
            if catalog == 'Online Campus Subscription':
                courses_df = courses_df[courses_df.course_key.isin(sq.oc_subs_catalog.course_key)]
            courses_df = courses_df.sort_values(by=['intersection_ratio','enrollment_count'], ascending=False)



            col1, col2, col3 = st.columns(3)

            with col1:
                st.write('**Course 1**')
                response = requests.get(courses_df.image_link.iloc[0])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[0]
                url = courses_df.url.iloc[0]
                title = courses_df.title.iloc[0]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=0)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 4**')
                response = requests.get(courses_df.image_link.iloc[3])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[3]
                url = courses_df.url.iloc[3]
                title = courses_df.title.iloc[3]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=3)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 7**')
                response = requests.get(courses_df.image_link.iloc[6])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[6]
                url = courses_df.url.iloc[6]
                title = courses_df.title.iloc[6]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=6)
                annotated_text(
                    *annots
                    )

            with col2:

                st.write('**Course 2**')
                response = requests.get(courses_df.image_link.iloc[1])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[1]
                url = courses_df.url.iloc[1]
                title = courses_df.title.iloc[1]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=1)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 5**')
                response = requests.get(courses_df.image_link.iloc[4])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[4]
                url = courses_df.url.iloc[4]
                title = courses_df.title.iloc[4]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=4)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 8**')
                response = requests.get(courses_df.image_link.iloc[7])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[7]
                url = courses_df.url.iloc[7]
                title = courses_df.title.iloc[7]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=7)
                annotated_text(
                    *annots
                    )

            with col3:

                st.write('**Course 3**')
                response = requests.get(courses_df.image_link.iloc[2])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[2]
                url = courses_df.url.iloc[2]
                title = courses_df.title.iloc[2]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=2)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 6**')
                response = requests.get(courses_df.image_link.iloc[5])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[5]
                url = courses_df.url.iloc[5]
                title = courses_df.title.iloc[5]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=5)
                annotated_text(
                    *annots
                    )

                st.write('')
                st.write('**Course 9**')
                response = requests.get(courses_df.image_link.iloc[8])
                image = Image.open(BytesIO(response.content))
                st.image(image, use_column_width=True)
                partner = courses_df.course_key.iloc[8]
                url = courses_df.url.iloc[8]
                title = courses_df.title.iloc[8]
                st.markdown(
                """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
                annots = annotations(df=courses_df, col1='skills',col2='intersection',index=8)
                annotated_text(
                    *annots
                    )
        else:
            st.write('Sorry that job is not well represented in the edX catalog. Try searching for another job.')



        




else:
    # Error handling to say there are no
    st.write("**No results for {}. Try expanding the date range, or choosing one of the following:**".format(company_name))
    st.write(eq.company_query(company_name))