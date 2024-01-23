import json
import random
import re
import openai
import datetime
import math
import pandas as pd
from urllib.parse import urlparse
from POC.browser_class import browser
import asyncio
from playwright.async_api import async_playwright
import time
import pyperclip
from serpapi import GoogleSearch
SERPAPI_API_KEY="66f816a51a51da9e957e40ca86f2c7c6ded19423f0c16cb862e1f9ea44518681"
profile_file = rf"C:\browsers_dir\shilo.json"


openai.api_key = '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'
openaiclient = openai.OpenAI(api_key=openai.api_key )

def extract_id_from_tweet_element(tweet):
    return re.search(r'status\/(.*?)"', tweet.inner_html()).group(1).split('/')[0]
def remove_historical_twitts(twitts, post_hist):
    post_hist=post_hist.fillna(0)
    if len(twitts)>0 and type(twitts[0])==dict and "id" in twitts[0].keys():
        twitts = [t for t in twitts if int(t['id']) not in list(post_hist["id"])]
        if len(twitts)==0:
            old=True
        else:
            old = False
    else:
        new_twitts=[]
        for t in twitts:
            if int(extract_id_from_tweet_element(t)) not in list(post_hist["id"]):
                print(extract_id_from_tweet_element(t))
                new_twitts.append(t)
                old=False
            else:
                old=True
        twitts=new_twitts
    return twitts,old

def sanitize_comment(comment: str) -> str:
    return comment.replace('\\n', '\n').replace('\\t', '\t').replace("Comment","").replace("comment","").replace(":","")


def sanitize_url(url: str) -> str:
    return url.replace('https', '').replace('http', '').replace('/', '').replace(':', '')


def load_persona():
    with  open("../persona.json", "r") as f:
        persona=json.load(f)
    return persona

def get_articles(query, language="en", file_type=None,location="Austin, Texas, United States"):
    # Define the filetype mapping
    SERPAPI_API_KEY = "66f816a51a51da9e957e40ca86f2c7c6ded19423f0c16cb862e1f9ea44518681"
    mapping = {
        "pdf": ["PDF", "DOC", "DOCX"],
        "excel": ["XLS", "XLSX", "CSV"],
        "powerpoint": ["PPT", "PPTX"],
        "articles": [""],
    }
    # Process each keyword
    # for keyword in keywords:
    #     query = '+'.join([f'"{x}"' for x in keyword.split(" ")])
    if file_type == "articles":
        pass
    else:
        # Append filetype to query if file_type is provided and valid
        if file_type in mapping:
            filetypes = mapping[file_type]
            filetype_queries = [f'filetype:{ft}' for ft in filetypes]
            query = query + " " + ' OR '.join(filetype_queries)
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "google_domain": "google.com",
        "gl": "us",
        "hl": language,
        "api_key": SERPAPI_API_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    file_data = results.get("organic_results", [])
    # Extract the dates from the search results
    if 'organic_results' in results:
        file_data = [
            {
                "title": new['title'],
                "snippet": new.get('snippet', ''),  # Use get() with a default value
                "source": new['source'],
                "link": new['link']
            }
            for new in file_data
        ]
    return file_data
def get_news(post):

    system="you are an expert in finding good up to date information via google searches"
    massage_History=[{"role":"system","content":system},
                     {"role":"user","content":f"Post:{post}"},
                     {"role":"user","content":f"from the previous post what is the best google search query need to find relevant information about the post"}]
    query=ask_gpt(massage_History,return_str=True)
    file_data=get_articles(query, language="en", file_type=None)
    return file_data


def get_news_raw(query, language, start_date, end_date):
    # Create a query string using the AND operator

    # Format the date range for the tbs parameter
    date_range = f'cdr:1,cd_min:{start_date},cd_max:{end_date}'

    params = {
        "engine": "google",
        "q": query,
        "tbs": date_range,
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
        {"date": new['date'],"title": new['title'], "snippet": new['snippet'], "source": new['source'], "link": new['link']}
        for new in news_results
    ]
    return news_data

def ask_bot_news(post):
    persona=load_persona()
    news=get_news(post)
    response = openaiclient.chat.completions.create(
      model="gpt-4-1106-preview",
      messages=[
        {
          "role": "system",
          "content": f"you are : {persona} (BTW the current date is {datetime.date.today().isoformat()} )\n always write in the style of your persona but never introduce yourself in your writing"
        },
        {
          "role": "user",
          "content": f"Post:{post}"
        },
        {
          "role": "user",
          "content": f"relevent news:{json.dumps(news)}"
        },
        {
          "role": "user",
          "content": f"write a replay TWEET to the tweet above if needed use the data in the articles provided,make tweet writing humuan like,be conclusive in you response,use persona only if its relvent,be direct, dont be polite,you can be sarcastic if needed,also very importent its a tweet  so maximum 270 characters are allowed mention someting about the risk of AI on humanity if relvent!"
        }
      ],
      temperature=0.2,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response.choices[0].message.content

def ask_gpt(massage_history,model="gpt-4-1106-preview",max_tokens=2000,temperature=0,return_str=True,response_format={"type": "json_object"}):

    response = openaiclient.chat.completions.create(
      model=model,
      messages=massage_history,
      response_format=response_format,
      temperature=temperature,
      max_tokens=max_tokens,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    if return_str:
        return response.choices[0].message.content
    else:
        return response

def ask_gpt_post(post):
    massage_history=[
        {
          "role": "system",
          "content": f"You are an AI influence you receive a post and write a comment with the goal of getting views , be a bit funny smart sophisticated , but not to much ,(BTW the current date is {datetime.date.today().isoformat()} )"
        },
        {
          "role": "user",
          "content": f"Post:{post}"
        }
      ]
    response=ask_gpt(massage_history, model="gpt-4-1106-preview", response_format={})
    return response
def get_comment(post: str) -> str:
    print(f"Got post {post}")


    return ask_bot_news(post)

def rand_int(mean,width):
    return round(random.gauss(mean,width/2))
def get_UTC_time(location):
    return 0
def get_engagment_params(type,location,today=datetime.date.today()):
    match (type.lower()):
        case "night":
            utc_shift=get_UTC_time(location)
            start_time=random.gauss(23,1)+utc_shift
            start_time=datetime.time(math.floor(start_time),(math.floor(start_time*60%60)),(math.floor(start_time*3600%60)))
            start_time=datetime.datetime.combine(today,start_time)
            end_time = random.uniform(0.5,1)
            end_time=start_time+datetime.timedelta(minutes=(math.floor(end_time * 60 % 60)),seconds=(math.floor(end_time * 3600 % 60)))

            Posts = random.randint(1,4)
            Reposts = random.randint(2,5)
            Replay = random.randint(4,10)
            Likes = random.randint(5,15)
        case _:
            return get_engagment_params("night",location,today)
    return {"start_time":start_time.isoformat(),"end_time":end_time.isoformat(),"posts":Posts,"reposts":Reposts,"replay":Replay,"likes":Likes}


def is_url(text):
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def extract_url_content(url):
    try:
        brsr = browser(profile_file=profile_file, sync=True)
        brsr.goto(url)
        time.sleep(5)  # Allow the page to load
        brsr.click_element('tag=body', first=True)
        brsr.page.keyboard.press('Control+A')
        brsr.page.keyboard.press('Control+C')
        copied_text = pyperclip.paste()  # Get copied text from clipboard
    except Exception as e:
        print(f"Error occurred: {e}")
        copied_text = None
    finally:
        brsr.close()

    return copied_text
async def url_analyzer(url):
    try:
        copied_text = extract_url_content(url) # Get copied text from clipboard

    except Exception as e:
        print(f"Error occurred: {e}")
        copied_text = None
    massage_history = [{"role": "system", "content": """You receive data collected from a url you job is the provide details bullet point summary of the main content in the url"""},
                       {"role": "user", "content": f"{copied_text}"}]
    responce = ask_gpt(massage_history)

    return responce

if __name__ == "__main__":
    dif=0

