import openai
# import fitz
import os
import pandas as pd
import json
import tabulate
import streamlit as st
from selenium import webdriver
from selenium.webdriver.firefox import firefox_profile
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import requests
import time
import pandas as pd
from io import StringIO

from serpapi import GoogleSearch
from collections import defaultdict



x="sk-9xPQ9C50b"
y="c1sYkg2yikQT3Bl"
z="bkFJ6jlVHQrpiJT3KZ9BmOMP"

openai.api_key = x+y+z
openaiclient = openai.OpenAI(api_key=openai.api_key )


def ask_gpt_vision(massage_history,temperature=0,max_tokens=3000):
    response = openaiclient.chat.completions.create(
        model="gpt-4-vision-preview",
        messages= massage_history,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
    )
    return response.choices[0].message.content

def ask_gpt(massage_history,model="gpt-4-1106-preview",max_tokens=2000,temperature=0,return_str=True,response_format={"type": "json_object"}):

    response =  openaiclient.chat.completions.create(
      model=model,
      messages=massage_history,
      response_format=response_format,
      temperature=temperature,
      max_tokens=max_tokens,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
    )
    if return_str:
        return response.choices[0].message.content
    else:
        return response
    

def get_news(query, language, start_date, end_date,tbm="nws"):
    SERPAPI_API_KEY="66f816a51a51da9e957e40ca86f2c7c6ded19423f0c16cb862e1f9ea44518681"


    params = {
        "engine": "google",
        "q": query,
        #"tbs": date_range,
        "location": "Austin, Texas, United States",
        "google_domain": "google.com",
        "gl": "us",
        "hl": language,
        "tbm": "nws",
        "api_key": SERPAPI_API_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    news_results = results.get("news_results", [])
    


    # Extract news results
    news_data = [
        {"date":new['date'], "title": new['title'], "snippet": new['snippet'], "source": new['source'], "link": new['link']}
        for new in news_results
    ]

    return news_data


def get_articles(query, language, start_date, end_date, file_type=None):
    # Define the filetype mapping
    SERPAPI_API_KEY="66f816a51a51da9e957e40ca86f2c7c6ded19423f0c16cb862e1f9ea44518681"

    final_df={}
    mapping = {
        "pdf": ["PDF", "DOC", "DOCX"],
        "excel": ["XLS", "XLSX", "CSV"],
        "powerpoint": ["PPT", "PPTX"],
        "articles": [""],
    }


    
    date_range = f'cdr:1,cd_min:{start_date},cd_max:{end_date}'

    
    # Initialize a dictionary to store the dates of articles
    article_dates = defaultdict(list)

     
    

    params = {
        "engine": "google",
        "q": query,
        "location": "Austin, Texas, United States",
        "google_domain": "google.com",
        "gl": "us",
        "hl": language,
        "api_key": SERPAPI_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    file_data = results.get("organic_results", [])
    processed_data = []
    for item in file_data:
        title = item.get('title', 'No Title')
        snippet = item.get('snippet', 'No Snippet')
        source = item.get('source', 'No Source')
        link = item.get('link', '#')

        processed_data.append({
            "title": title,
            "snippet": snippet,
            "source": source,
            "link": link
        })

    return processed_data



def markdown_to_df(text):
    # Remove table formatting (| and -) from the input text
    cleaned_text = text.replace("|", "").replace("-", "")
    
    # Use StringIO to read the cleaned string as if it were a file
    data = StringIO(cleaned_text)
    
    # Read the data into a DataFrame
    df = pd.read_csv(data, sep="\s{2,}", engine='python')
    return df



# def extract_text(pdf_path):
#     doc = fitz.open(pdf_path)
#     text = ""
#     for page in doc:
#         text += page.get_text()
#     doc.close()
#     return text

# def truncate_after_phrase(text, phrase):
#     index = text.find(phrase)
#     if index != -1:  # Phrase found
#         return text[:index]  # Return text up to the phrase
#     else:
#         return text
# def create_clean_text_dir(pdf_dir, clean_text_dir):
#     # Create the clean_text directory if it doesn't exist
#     if not os.path.exists(clean_text_dir):
#         os.makedirs(clean_text_dir)

#     # Iterate through the PDFs in the pdf_dir
#     for pdf_file in os.listdir(pdf_dir):
#         if pdf_file.endswith('.pdf'):
#             # Extract the text from the PDF
#             text = extract_text(os.path.join(pdf_dir, pdf_file))

#             # Truncate the text after the "References" section
#             text = truncate_after_phrase(text, "References")

#             # Construct the .txt filename based on the original PDF filename
#             txt_filename = pdf_file.replace(".pdf", ".txt")

#             # Write the clean text to a file
#             with open(os.path.join(clean_text_dir, txt_filename), "w", encoding="utf-8") as f:
#                 f.write(text)



#main
if __name__ == "__main__":
    # text=extract_text("../pdfs/alex_prudhomme_uri_2022.pdf")
    # text=truncate_after_phrase(text,"References")
    # print(text)
    # response=ask_gpt([{"role": "system", "content": "Summarize the following text output json format"},{"role": "user", "content": text}],return_str=True,model="gpt-4-1106-preview",max_tokens=3000,temperature=1)
    # print(response)

    # pdf_dir = r"C:\Users\user\PycharmProjects\mscience\app\pdfs"  # Replace with the path to your PDF directory
    # clean_text_dir = r"C:\Users\user\PycharmProjects\mscience\app\clean_text"
    # create_clean_text_dir(pdf_dir, clean_text_dir)
    print(get_articles(["covid-19"], "en", "2020-01-01", "2021-01-01", file_type="articles"))
    
    



