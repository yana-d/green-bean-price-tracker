#!/usr/bin/env python
# coding: utf-8

# In[2]:


# Imports standart packages
import pandas as pd 

import seaborn as sns
import matplotlib.pyplot as plt

import requests
from bs4 import BeautifulSoup

# E-mail notifictions packages
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Custom imports
import config as cfg 

# URL of our target page we gonna scrap
url = "https://offerlist.rehmcoffee.de"

# Creating session
s = requests.Session()

# Using Requests's method get on session object to get access to the page content
login_form = s.get(url)

# Creating soup object
soup_login_form = BeautifulSoup(login_form.content,"html5lib")

# Search for inputs that are required to be submitted to the login form to pass it
list_input = soup_login_form.find_all("input")

token_nr1 = soup_login_form.find("input", {"name":"logintype"})["value"]
token_nr2 = soup_login_form.find("input", {"name":"pid"})["value"]
token_nr3 = soup_login_form.find("input", {"name":"redirect_url"})["value"]
token_nr4 = soup_login_form.find("input", {"name":"tx_felogin_pi1[noredirect]"})["value"]

# Fail config.py stores sensitive data: usernames and passwords in following line:
# login_data = {'user': 'name@company-name.com', 'pass': 'password_received_from_trader'}

# login_data = {"user":"mymail@company-name.com", "pass":"your_password", "logintype":token_nr1, "pid":token_nr2, "redirect_url":token_nr3, "tx_felogin_pi1[noredirect]":token_nr4}
login_data = cfg.login_data
login_data["logintype"] = token_nr1
login_data["pid"] = token_nr2
login_data["redirect_url"] = token_nr3
login_data["tx_felogin_pi1[noredirect]"] = token_nr4

# Creating post request
s.post(url, login_data)

offer_page = s.get(url)

# Pass HTML into the BeautifulSoup constructor, then create a new BeautifulSoup object : soup_offer_page
soup_offer_page = BeautifulSoup(offer_page.content,"html5lib")


# Checking how many tables are on page
tables = soup_offer_page.find_all('table')

# Loop that search for word in tables and prints an index of a table 
for index,table in enumerate(tables):
    if ("almond" in str(table)):
        table_index = index
        
# The function read_html always returns a list of DataFrames so we must pick the one we want out of the list
# We use [0] index as we already spicified proper table from tables above
offer_list_rehm_df = pd.read_html(str(tables[table_index]), flavor='bs4')[0]

# Below we will add date when we scrapped new update
current_date = pd.to_datetime('today').normalize()

offer_list_rehm_df['offer_date'] = current_date

offer_list_rehm_df_copy = offer_list_rehm_df.copy(deep=True)

# Create function to clean column values 
def clean_unit_col(x):
    x = x.replace("kg", "").replace(" ", "")
    return int(x)

def clean_eur_col(y):
    y = y.replace("€", "").replace(",", ".").replace(" ", "")
    return round(float(y),2)

def clean_usd_col(z):
    z = z.replace("$", "").replace(",", ".").replace(" ", "")
    return round(float(z),2)

# Cleaning column values in scrapped data
offer_list_rehm_df_copy['Unit'] = offer_list_rehm_df_copy['Unit'].apply(clean_unit_col)

offer_list_rehm_df_copy['€ / KG'] = offer_list_rehm_df_copy['€ / KG'].apply(clean_eur_col)

offer_list_rehm_df_copy['$ / KG'] = offer_list_rehm_df_copy['$ / KG'].apply(clean_usd_col)

# Appending new scrapped data to existing .csv fail 
offer_list_rehm_df_copy.to_csv('scraped-data/rehm-offer-list-test.csv',mode='a',index=False,header=False)


# Reading whole file where offers from different dates are stored
test_df = pd.read_csv('scraped-data/rehm-offer-list-test.csv')

# Filling in email body
email_body = "<html><body>Hey folks! That's green-bean-price-tracker bot here. I've just completed the fresh tasty updates to Rehm's coffee offers list from: "
email_body += str(current_date)
email_body += "<br>We've got "
email_body += str(len(offer_list_rehm_df_copy))
email_body += "new coffee offers this week. By that moment we collected offers from following dates:"
email_body += str(test_df['offer_date'].unique())
email_body += ". All together are "
email_body += "rows."
email_body += str(len(test_df))
email_body += '<br>Yours green-bean-price-tracker bot</body></html>'

# Email Account
email_sender_account = cfg.email_sender_account # email_sender_account = "your.registered.name@gmail.com"
email_sender_username = cfg.email_sender_username # email_sender_username = "your.registered.name"
email_sender_password = cfg.email_sender_password # email_sender_password = "your_gmail_password"
email_smtp_server = "smtp.gmail.com" # SMTP, eg smtp.gmail.com for gmail
email_smtp_port = 587 # SMTP Porf, eg 587 for gmail

# Email Content
email_recepients = ["yana.dzhulay@dbf-regensburg.de","mail@dbf-regensburg.de"]
email_subject = "test notification - weekly updates - green-bean-price-tracker "

# login to email server
server = smtplib.SMTP(email_smtp_server,email_smtp_port)
server.starttls()
server.login(email_sender_username, email_sender_password)

# loop through all email recipients
for recipient in email_recepients:
    print("Sending email to: " , recipient)
    message = MIMEMultipart('alternative')
    message['From'] = email_sender_account
    message['To'] = recipient
    message['Subject'] = email_subject
    message.attach(MIMEText(email_body, 'html'))
    text = message.as_string()
    server.sendmail(email_sender_account,recipient,text)
    
# Log out
server.quit()

