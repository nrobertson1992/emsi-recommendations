# Use what you learned in mortgage.py to make magic happen.

# For calling the API and manipulating data.
import requests
import numpy as np
import pandas as pd
import json

# For making beautiful visuals.
import altair as alt

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

# Entry paragraph.
st.write("This is an internal tool, designed first for marketing, to help them find top skills and jobs in certain industries and companies, as well as courses those industries and companies might be interested in. The goal is to use this information to drive activities such as: A/B language tests on LinkedIn Campaigns, targeted Account-Based Marketing outreach, enable experiments of matching content to prospects based on the skill trends at their organization.")


# Start of the sidebar.
st.sidebar.subheader('Details')

# Radio button to select search facet -- company, or industry.
search = st.sidebar.radio(
     "How would like to search?",
     ('By Company', 'By Industry'))

# If company, company_name is a sidebar text input (default: IBM).
if search == 'By Company':
     company_name = st.sidebar.text_input("Enter the company you are searching for:", "IBM")
     industry_name = '' # You do this to make it easier to handle company vs. industry later. Is there a better way?
     naics_level = None # You do this to make it easier to handle company vs. industry later. Is there a better way?

# If industry, naics_level is a sidebar select box (only NAICS2 supported for now).
# If NAICS level is 2, then populate the industry_name with a select sidebar from the NAICS 2 dictionary.
elif search == 'By Industry':
     naics_level = st.sidebar.selectbox("What level of NAICS industry are you searching? (only 2 and 3 supported)", ("2","3"))
     if naics_level == "2":
         industry_name = st.sidebar.selectbox("Enter the NAICS industry you are searching for:", tuple(sorted(eq.naics2_dictionary.keys())))
         company_name = '' # You do this to make it easier to handle company vs. industry later. Is there a better way?
     if naics_level == "3":
         industry_name = st.sidebar.selectbox("Enter the NAICS industry you are searching for:", tuple(sorted(eq.naics3_dictionary.keys())))
         company_name = '' # You do this to make it easier to handle company vs. industry later. Is there a better way?



# Fill out the rest of the sidebar, which does not rely on conditional logic.
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

# Generate the emsi dataframe based on what is the focus - job or skill.
if metric == "skills":
    emsi_df = eq.get_top_skills(start_date=start_date,end_date=end_date,company_name=company_name, 
                                sort=sort, search_type=search, industry_name=industry_name, naics=naics_level)
if metric == "jobs":
    emsi_df = eq.get_top_jobs(start_date=start_date,end_date=end_date,company_name=company_name, 
                              sort=sort, search_type=search, industry_name=industry_name, naics=naics_level)


# If there is at least one result in the dataframe, then execute the following.
if len(emsi_df) > 0:

    # Show Altair bar char of top 10 [skills|jobs] by [company|industry].
    st.subheader('Labor Market Analysis')
    st.write('Top 10 {} for {}, ranked by {}, from {} to {}.'.format(metric, company_name + industry_name, sort, start_date, end_date))
    c = alt.Chart(emsi_df).mark_bar().encode(
                x=alt.X(sort), 
                y=alt.Y(metric, sort='-x'),
                tooltip=[sort]
            )
  
    # Execute chart.
    st.altair_chart(c, use_container_width=True)

    # Get a list of all of the edX courses with >=100 enrolls, and what they teach.
    courses_df = sq.get_snowflake_data(query=sq.sql1, columns=sq.cols1)

    # Transform the column's data structure to lists.
    def listify(x):
        return list(x.split(', '))

    # Apply the function.
    courses_df['skills'] = courses_df['skills'].apply(listify)

    # Similarity algorithm 1: intersection ratio.
    def intersection_ratio(set_a, set_b):
        intersection = set_a.intersection(set_b)
        intersection_ratio = len(intersection)/len(set_a)
        return intersection_ratio

    # Outputs intersecting skills from similarity algorithm 1.
    def intersection(set_a, set_b):
        intersection = set_a.intersection(set_b)
        return list(intersection)

    # Handles skill annotations, and color coding skills that intersect.
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

    # Subheader for edX course recommendations.
    st.subheader('Top Recommended edX Courses for {}'.format(company_name + industry_name))

    # You'll use this repeatedly below to call each of the course cards in the result set
    # you want to show.
    def course_card(idx):
            st.write('**Course {}**'.format(idx+1))
            response = requests.get(courses_df.image_link.iloc[idx])
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
            partner = courses_df.course_key.iloc[idx]
            url = courses_df.url.iloc[idx]
            title = courses_df.title.iloc[idx]
            st.markdown(
            """<a href="{}">{}: {}</a>""".format(url, partner, title), unsafe_allow_html=True)
            annots = annotations(df=courses_df, col1='skills',col2='intersection',index=idx)
            annotated_text(
                *annots
                )

    # Create downloadable dataframe.
    def convert_df(df):
        return df.to_csv().encode('utf-8')

    # If the metric we are looking at is skills, execute the following.
    if metric == 'skills':

        col1, col2 = st.columns(2)
        # Allow the user to filter the catalog by catalog type.
        with col1:
            catalog = st.selectbox("Filter by catalog.", ("All edX Courses","Business Subscription","Online Campus Subscription"))
        with col2:
            partner = st.multiselect("Filter by partner", options=sorted(courses_df.partner.unique()))

        # Filter out courses not included in the partner filter.
        if len(partner) > 0:
            courses_df = courses_df[courses_df.partner.isin(partner)]

        # Filter out courses not included in the catalog. Skill if catalog is "All edX Courses."
        if catalog == 'Business Subscription':
            courses_df = courses_df[courses_df.course_key.isin(sq.b2b_subs_catalog.course_key)]
        if catalog == 'Online Campus Subscription':
            courses_df = courses_df[courses_df.course_key.isin(sq.oc_subs_catalog.course_key)]

        # Appy the similarity algorithms.
        courses_df['intersection_ratio'] = [intersection_ratio(set_a=set(emsi_df[metric]), set_b=set(set_b)) for set_b in courses_df.skills]
        courses_df['intersection'] = [intersection(set_a=set(emsi_df[metric]), set_b=set(set_b)) for set_b in courses_df.skills]

        # Sort values by similarity algorithm and enrollment count.
        courses_df = courses_df.sort_values(by=['intersection_ratio','enrollment_count'], ascending=False)

        csv = convert_df(courses_df)

        st.download_button(
           "Download all Courses",
           csv,
           "results.csv",
           "text/csv",
           key='download-csv'
            )

        # You can probably find a better way of executing this. Try to wrap it into a function!
        col1, col2, col3 = st.columns(3)

        # Show the first column of cards.
        with col1:
            course_card(idx=0)
            st.write('')
            course_card(idx=3)
            st.write('')
            course_card(idx=6)

        # Show the second column of cards.
        with col2:
            course_card(idx=1)
            st.write('')
            course_card(idx=4)
            st.write('')
            course_card(idx=7)

        # Show the third column of cards.
        with col3:
            course_card(idx=2)
            st.write('')
            course_card(idx=5)
            st.write('')
            course_card(idx=8)


    # If the metric are looking at is jobs, execute the following.
    if metric == 'jobs':

        # We have multiple search filters for this one at this time. Let's build two columns.
        col1, col2 = st.columns(2)

        with col1:
            # Filter for the catalog type.
            catalog = st.selectbox("Filter by catalog.", ("All edX Courses","Business Subscription","Online Campus Subscription"))
            partner = st.multiselect("Filter by partner", options=courses_df.partner.unique())

        with col2:
            # Some wonkiness. The job titles in the labor market queries are plural, but the job titles in edX ingested data is
            # singular. For now, I'm just going to use an off the shelf package to strip the plural down to singular. Doing some
            # basic testing, it looks like it matches.
            def singularize(x):
                return p.singular_noun(x)
            emsi_df['jobs'] = emsi_df['jobs'].apply(singularize)

            # The only jobs that will be available are the top 10 jobs shown in the chart.
            job = st.selectbox("Filter by top job.", (emsi_df.jobs.values))

        # Get the job-skill relationships out for only the jobs that are selected. 
        job_skills = sq.job_skills_mapping[sq.job_skills_mapping['job_name'] == job][['skill_name']]

        # If there is at least one result.
        if len(job_skills) > 0:

            # Filter out courses not included in the partner filter.
            if len(partner) > 0:
                courses_df = courses_df[courses_df.partner.isin(partner)]

            # Filter based on catalog type selection.
            if catalog == 'Business Subscription':
                courses_df = courses_df[courses_df.course_key.isin(sq.b2b_subs_catalog.course_key)]
            if catalog == 'Online Campus Subscription':
                courses_df = courses_df[courses_df.course_key.isin(sq.oc_subs_catalog.course_key)]

            # Calculate similarity ratios.
            courses_df['intersection_ratio'] = [intersection_ratio(set_a=set(job_skills['skill_name']), set_b=set(set_b)) for set_b in courses_df.skills]
            courses_df['intersection'] = [intersection(set_a=set(job_skills['skill_name']), set_b=set(set_b)) for set_b in courses_df.skills]
            
            # Sort results by similarity algorithms.
            courses_df = courses_df.sort_values(by=['intersection_ratio','enrollment_count'], ascending=False)


            csv = convert_df(courses_df)

            st.download_button(
               "Download all Courses",
               csv,
               "results.csv",
               "text/csv",
               key='download-csv'
                )



            col1, col2, col3 = st.columns(3)

            # Show the first column of cards.
            with col1:
                course_card(idx=0)
                st.write('')
                course_card(idx=3)
                st.write('')
                course_card(idx=6)

            # Show the second column of cards.
            with col2:
                course_card(idx=1)
                st.write('')
                course_card(idx=4)
                st.write('')
                course_card(idx=7)

            # Show the third column of cards.
            with col3:
                course_card(idx=2)
                st.write('')
                course_card(idx=5)
                st.write('')
                course_card(idx=8)
        else:
            # If the job_name can't be found discovery_pii's taxonomy of Emsi, say this.
            st.write('Sorry that job is not well represented in the edX catalog. Try searching for another job.')


else:
    # Error handling to say there are no results. Typically, this is because the company submitted is wrong.
    st.write("**No results for {}. Try expanding the date range, or choosing one of the following:**".format(company_name))
    st.write(eq.company_query(company_name))