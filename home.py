
from config import *
import openai
import os
import time
import pandas as pd
import json
import re
import time
import datetime as dt
from datetime import datetime, timedelta




st.set_page_config(layout="wide")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4-1106-preview"

if "openai_model_onbot" not in st.session_state:
    st.session_state["openai_model_onbot"] = "gpt-4-1106-preview"
    

if "chosen_keys_for_expanders" not in st.session_state:
    st.session_state["chosen_keys_for_expanders"] = []

def chat_process(prompt,massage_history="",write_contetn=False):
    st.session_state.messages_QNA_bot.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
    
        message_placeholder = st.empty()
        full_response = ""
        for response in openaiclient.chat.completions.create(
            model=st.session_state["openai_model"],
            stream=True,
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages_QNA_bot],
        ):
            # Check for content and finish reason
            if response.choices[0].delta.content is not None:
                full_response += response.choices[0].delta.content
                message_placeholder.write(full_response + "▌")
            if response.choices[0].finish_reason is not None:
                break

        message_placeholder.write(full_response)
    st.session_state.messages_QNA_bot.append({"role": "assistant", "content": full_response})
    st.rerun()
    with st.sidebar.expander("✔️ Complete ", expanded=False):
        st.write("Process finished successfully! Here are some articles related to 'Can Humans Be AI Themselves?':")
      

    if st.session_state["chosen_keys_for_expanders"]!=[]:
      recrate_expander(st.session_state["chosen_keys_for_expanders"])


    start_index = 5 
    for index, message in enumerate(st.session_state.messages_QNA_bot):
        if index < start_index:
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])


data_dict={
    "Balance Sheets":"""The provided raw data represents a detailed balance sheet of a company named UserWay, encompassing various critical financial elements:

1. **Asset Overview**: It splits assets into current and non-current categories, with specific values and monthly (M_M) and yearly (Y_Y) changes. The current assets are further detailed with components like prepaid expenses and trade receivables, while non-current assets include items such as electronic equipment and intangible assets.

2. **Liabilities Breakdown**: The data shows current and non-current liabilities, again with specific values and change rates. It details various liabilities like credit cards, short-term loans, and supplier credits.

3. **Financial Ratios and Totals**: Key financial ratios such as the current ratio and debt-to-equity ratio are provided, offering insights into the company's liquidity and financial leverage. The total values of assets and liabilities are also included.

4. **Equity Information**: It provides the company's total equity value, along with its month-over-month and year-over-year changes.

5. **Pie Charts Data**: The data includes pie chart breakdowns for current assets, current liabilities, non-current assets, and non-current liabilities, showing the proportion of each component.

6. **Global Growth Rates**: The data outlines the global growth rates for assets and liabilities, both on a monthly and yearly basis.

7. **Working Capital**: It calculates the working capital of the company and provides its monthly and yearly changes.

This balance sheet data is crucial for understanding the company's financial health, analyzing its asset management, liability structure, and overall financial stability. This information is vital for investors, financial analysts, and the company's management for decision-making and strategic planning.""",
    "Cash Flow":"""The provided raw data offers a comprehensive cash flow analysis for a company named UserWay. This analysis covers various aspects:

1. **CapEx Information**: Highlights UserWay's capital expenditures, crucial for understanding its investments in long-term assets.

2. **Current Ratio**: Provides a measure of UserWay's short-term liquidity, comparing current assets to current liabilities.

3. **Cash Flow Details**: Showcases UserWay's cash flow at the start and end of the month, reflecting its cash management effectiveness.

4. **Financial and Investing Activities**: Breaks down UserWay's financial and investing activities and expenses, offering insights into how the company allocates its financial resources.

5. **Operating Expenses and Activities**: Details the company's operating expenses and activities, including changes in various operational financial items.

6. **Net Burn Rate**: Presents UserWay's net burn rate, indicating the rate at which the company is utilizing its cash reserves.

7. **Charts and Breakdowns**: Contains detailed charts and breakdowns of finance, investing, and operating activities, providing a granular view of UserWay's financial operations.

This cash flow analysis is essential for stakeholders to assess UserWay's financial health, operational efficiency, investment strategies, and overall management of cash flows.""",
    "PNL":"""Certainly! For the Profit and Loss (P&L) analysis of UserWay, the following comprehensive review can be offered:

The provided data presents a detailed Profit and Loss analysis for UserWay, covering several key financial dimensions. This analysis includes:

1. **Revenue Streams**: It breaks down various revenue sources, illustrating how much each segment contributes to the total revenue. This information is crucial for identifying which areas of UserWay's business are the most profitable.

2. **Expense Allocation**: The data details the distribution of expenses across different categories such as sales and marketing, research and development (R&D), general and administrative, and cost of goods sold. This aspect is essential for understanding how resources are allocated and identifying the most significant areas of expenditure.

3. **Operational Efficiency**: Key financial metrics included in the analysis are gross margin, net margin, operating margin, and year-to-date revenue growth. These metrics provide insights into UserWay's operational efficiency and profitability.

4. **Financial Performance Over Time**: The analysis includes growth rates for both revenue and expenses, which are critical for assessing UserWay's financial performance over time. Additionally, year-over-year growth figures offer a comparative perspective of the company's financial evolution.

5. **Comprehensive Overview**: This P&L analysis serves as a vital tool for stakeholders, including investors, managers, and analysts, to understand the financial health and performance of UserWay. It aids in identifying strengths, areas needing improvement, and overall financial strategy effectiveness.

By examining these aspects, the P&L analysis provides a holistic view of UserWay's financial standing, allowing for informed decision-making and strategic planning.""",
    "Goverment Payments":"""The provided data offers a financial comparison between current and previous periods for a company, with figures in both New Israeli Shekels (NIS) and United States Dollars (USD). The data covers three key financial areas:

1. **VAT (Value Added Tax)**: Shows the VAT figures for both the current and previous periods. In NIS, there's an increase from a negative to a positive figure, indicating a shift from a VAT refundable position to a VAT payable one. In USD, a similar trend is observed, with the figures moving from negative to positive.

2. **Social Security**: This item is marked as "On Client Reports" for both periods in both currencies, suggesting that the details for social security contributions are reported elsewhere or in a different format.

3. **Payroll Taxes Accrual**: Represents the accrual of payroll taxes. In both NIS and USD, there's an increase in payroll taxes accrual from the last period to the current one, indicating a rise in payroll tax obligations.

This data is crucial for understanding the company's tax liabilities and payroll tax commitments over the two periods, providing insights into its financial obligations and operational costs in these areas."""}

Balance_Sheets_path="""company data//Balance Sheets//raw.json"""
Cash_Flow_path="""company data//Cash Flow//raw.json"""
PNL_path="""company data//PNL//raw.json"""
Goverment_Payments_path="""company data//Goverment Payments//raw.json"""

#extract the data 
with open(Balance_Sheets_path, 'r') as file:
    Balance_Sheets= file.read()
with open(Cash_Flow_path, 'r') as file:
    Cash_Flow = file.read()
with open(PNL_path, 'r') as file:
    PNL = file.read()
with open(Goverment_Payments_path, 'r') as file:
    Goverment_Payments = file.read()
    

q_and_a_massage_history=[{"role":"system","content":f"You are an ai Accoutent will get from the user a question and relvent data for the question you goal is the answer the question based on this data in a proffesinal manner in a nicely strectured way"},
                         {"role":"user","content":f"**THIS IS THE BALANCE SHEETS DATA**: {Balance_Sheets}"},
                         {"role":"user","content":f"**THIS IS THE Cash Flow DATA**: {Cash_Flow}"},
                         {"role":"user","content":f"**THIS IS THE PNL DATA**: {PNL}"},
                         {"role":"user","content":f"**THIS IS THE Goverment Payments DATA**: {Goverment_Payments}"},
                         {"role":"assistant","content":"Welcome to your interactive online deck! Feel free to ask any questions about our company, including our roadmap, and financial projections."}]




if "messages_QNA_bot" not in st.session_state:
    st.session_state["messages_QNA_bot"]=q_and_a_massage_history

def create_expnaders(prompt):
    system_get_keys="You will get user question , and a data dict where the key is the excplict name of the datapoint and the value is the explination of the datapoint, you need to output in json format they keys that you think they data inside on the datapoint is relvent for answering the question , the json should have a key name 'answer' amd the value is a python list with explicit names of the keys of the datpoints you think are relvent for the answer Note you can use more than 1 datapoint for the answer"

    get_keys_massage_history=[{"role":"system","content":system_get_keys},
                            {"role":"user","content":f"***THIS IS THE USER QUESTION**: {prompt}"},
                            {"role":"user","content":f"***THIS THE DATA DICT**: {data_dict}"}]

    response=ask_gpt(get_keys_massage_history)
    response=json.loads(response)
    table_to_show=response["answer"]   
    st.session_state["chosen_keys_for_expanders"] = table_to_show

    if "expanders_state" not in st.session_state:
        st.session_state["expanders_state"] = {} 
    for key in table_to_show:
        summury_path=f"company data/{key}/summury.txt"
        with open(summury_path, 'r') as file:
            summury_text = file.read()
       
        with st.expander(key, expanded=False):
            #print text using markdwon
            st.markdown(summury_text, unsafe_allow_html=True)


        with st.expander(f"Data Tables {key}", expanded=False):
            file_path=f"company data/{key}"
            #get all .csv from dir create path list
            files = [os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith('.json')]
            #print all as dataframe use csv name as title
            for file in files:
                with st.container(border=True):
                    #replace none with 0 and first name add Month 1....Month 18
                    file_content=json.load(open(file))
                    st.write(os.path.basename(file))
                    
                    st.json(file_content)
                    

                    


def create_expnaders_key(prompt):
    system_get_keys="""You will get user question , and a data dict where the key is the excplict name of the datapoint and the value is the explination of the datapoint, you need to output in json format they keys that you think they data inside on the datapoint is relvent for answering the question , the json should have a key name 'answer' amd the value is a python list with explicit names of the keys of the datpoints you think are relvent for the answer Note you can use more than 1 datapoint for the answer"""
    get_keys_massage_history=[{"role":"system","content":system_get_keys},
                            {"role":"user","content":f"***THIS IS THE USER QUESTION**: {prompt}"},
                            {"role":"user","content":f"***THIS THE DATA DICT**: {data_dict}"}]

    response=ask_gpt(get_keys_massage_history)
    response=json.loads(response)
    
    table_to_show=response["answer"]   
    st.session_state["chosen_keys_for_expanders"] = table_to_show
                     
                     
def recrate_expander(keys):
    for key in keys:
        summury_path=f"company data/{key}/summury.txt"
        with open(summury_path, 'r') as file:
            summury_text = file.read()
        if key not in st.session_state["expanders_state"]:
            st.session_state["expanders_state"][key] = False

        with st.expander(key, expanded=False):
            #print text using markdwon
            st.markdown(summury_text, unsafe_allow_html=True)
            st.session_state["expanders_state"][key] = not st.session_state["expanders_state"][key]


        with st.expander(f"Data Tables {key}", expanded=False):
            file_path=f"company data/{key}"
            #get all .csv from dir create path list
            files = [os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith('.csv')]
            #print all as dataframe use csv name as title
            for file in files:
                with st.container(border=True):
                    #replace none with 0 and first name add Month 1....Month 18
                    file_content=json.load(open(file))
                    st.write(os.path.basename(file))
                    
                    st.json(file_content)


    
x="sk-9xPQ9C50b"
y="c1sYkg2yikQT3Bl"
z="bkFJ6jlVHQrpiJT3KZ9BmOMP"

st.title("AcountBot🤖")

openai.api_key = x+y+z

openaiclient = openai.OpenAI(api_key=openai.api_key )

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
    


# Render the expanders first if the keys are set
if st.session_state["chosen_keys_for_expanders"] != []: 
    recrate_expander(st.session_state["chosen_keys_for_expanders"])

# Placeholder for chat messages
chat_QNAbot_placeholder = st.empty()

# Render chat messages
with chat_QNAbot_placeholder.container():
    start_index = 5
    for index, message in enumerate(st.session_state.messages_QNA_bot):
        if index < start_index:
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Handle user input
if prompt := st.chat_input("Type Here"):
    if st.session_state["chosen_keys_for_expanders"] != []: 
        create_expnaders_key(prompt)
    else:
        create_expnaders(prompt)
    chat_process(prompt)
                          
  
