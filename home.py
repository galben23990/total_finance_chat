import streamlit as st
import pandas as pd
import os
import datetime
import chardet
from scripts import create_BS_table, create_PNL_table, get_data, create_pie_chart, process_spreadsheet,create_cash_flow_statement
import matplotlib as mpl

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def format_cash_flow(value):
    # Check if the value is negative or positive to assign color
    color = "red" if value < 0 else "green"
    # Format the value as currency with NIS symbol and 2 decimal places
    formatted_value = "NIS {:,.2f}".format(value)
    return f"<span style='color: {color};'>{formatted_value}</span>"

def format_delta(value):
    if value == 0:
        # Handling zero delta (can change the string to "No change" if preferred)
        return 0
    else:
        # Format the value with two decimal places and prepend the currency symbol
        return round(float(value), 2)
# Define your report visualization function
def visualize_report(report_df, report_type):
    st.title(f"{report_type} September 2023")
    # Add your visualization logic here
    # For example, you might use st.line_chart, st.bar_chart, etc.
    st.dataframe(report_df)  # Placeholder for actual visualization


# Modify your process_data function (if needed)
# Modify your process_data function with mock logic for demonstration
def process_data(report_type, account_coding_df, code_total_df):
    # Implement processing logic
    if report_type == "PNL":
        processed_df = create_PNL_table(account_coding_df, code_total_df)
    elif report_type == "BS":
        processed_df = code_total_df.copy()  # Replace with actual logic
    elif report_type == "CF":
        processed_df = pd.concat([account_coding_df, code_total_df])  # Replace with actual logic
    # Add your actual data processing logic here
    return processed_df


def filter_dataframe(df, key):
    st.sidebar.header(f"Filter {key} options")
    filtered_df = df
    for col in df.columns:
        # Check for NaN values and replace them with a string for filtering purposes
        df[col] = df[col].fillna('None')
        unique_values = df[col].unique().tolist()

        # Convert all values to string for consistency in the multiselect widget
        unique_values = [str(value) for value in unique_values]

        # Selectbox/multiselect per column
        selected = st.sidebar.selectbox(f"Filter by {col}:", ["All"] + unique_values, key=f"{key}_{col}")
        if selected != "All":
            # Filter the dataframe based on the selection
            filtered_df = filtered_df[filtered_df[col].astype(str) == selected]

    return filtered_df


# Callback function to add an email to the list without refreshing
def add_email():
    if st.session_state.email_input and st.session_state.email_input not in st.session_state.email_list:
        st.session_state.email_list.append(st.session_state.email_input)
        st.session_state.email_input = ""  # Reset the input field


# Callback function to process and share the report
def share_report():
    if 'email_list' in st.session_state and st.session_state.email_list:
        # Here you would call your process_spreadsheet function
        process_spreadsheet(st.session_state.pnl_report, st.session_state.email_list)
        st.success("Report shared successfully!")
        st.session_state.email_list = []  # Clear the list after sharing


def remove_email(email_to_remove):
    st.session_state.email_list.pop(index)


st.set_page_config(layout="wide")
# Define the custom CSS block
css = """
<style>
    body {
        color:#A7C7E7;
    }
    h1 {
        color:#A7C7E7;
    }
    h2 {
        color:#A7C7E7;
    }
    h3 {
        color:#A7C7E7;
    }
    h4 {
        color:#A7C7E7;
    }
    h5 {
        color:#A7C7E7;
    }
    h6 {
        color:#A7C7E7;
    }
     .stButton > button {
    color:#A7C7E7 !important;
    size: 20px;
    bold: True;
    }
    .stExpander > button {
    color:#A7C7E7 !important;
    }
    .st-expander-header .st-expander-button {
        color:#A7C7E7 !important;
    }

    /* Style expander content border */
    .st-expander-label {
        border: 2px solid#A7C7E7 !important;
    }
</style>
"""

# Apply the custom CSS block using st.markdown
st.markdown(css, unsafe_allow_html=True)
if 'email_list' not in st.session_state:
    st.session_state['email_list'] = []

# Navigation
if "navigation" not in st.session_state:
    st.session_state["navigation"] = "home"

# Home page layout
if st.session_state["navigation"] == "home":
    # titile wuth #F5E1FD
    st.markdown("<h1 style='text-align: center; color:#A7C7E7;'>Total Finance Report Creator</h1>",
                unsafe_allow_html=True)
    # Initialize session state variables for dataframes
    if 'account_coding_df' not in st.session_state:
        st.session_state['account_coding_df'] = None
    if 'code_total_df' not in st.session_state:
        st.session_state['code_total_df'] = None

    col1, col2, col3 = st.columns(3)  # Create two columns for upload buttons
    with col1:
        st.markdown("<h4 style='text-align: center; color:#A7C7E7;'>Upload Account Coding</h1>",
                    unsafe_allow_html=True)
        with st.expander(" ", expanded=True):
            uploaded_account_coding = st.file_uploader(" ", type=['csv'], key="account_coding")
            if uploaded_account_coding is not None:
                st.session_state['account_coding_df'] = pd.read_csv(uploaded_account_coding)
                st.success("Account Coding uploaded!")
                # Filter the Account Coding dataframe with its own unique expander
                #st.session_state['account_coding_df'] = filter_dataframe(st.session_state['account_coding_df'], 'account_coding')
                st.dataframe(st.session_state['account_coding_df'])

    with col2:
        st.markdown("<h4 style='text-align: center; color:#A7C7E7;'>Upload Code Total</h1>", unsafe_allow_html=True)
        with st.expander(" ", expanded=True):
            uploaded_code_total = st.file_uploader(" ", type=['csv'], key="code_total")
            if uploaded_code_total is not None:
                st.session_state['code_total_df'] = pd.read_csv(uploaded_code_total)
                st.success("Code Total uploaded!")
                # Filter the Code Total dataframe with its own unique expander
                #st.session_state['code_total_df'] = filter_dataframe(st.session_state['code_total_df'], 'code_total')
                st.dataframe(st.session_state['code_total_df'])

    with col3:
        st.markdown("<h4 style='text-align: center; color:#A7C7E7;'>Upload Balance Sheet Files</h1>",
                    unsafe_allow_html=True)
        with st.expander(" ", expanded=True):
            uploaded_balance_sheet = st.file_uploader(" ", type=['csv'], key="balance_sheet")
            if uploaded_balance_sheet is not None:
                st.session_state['balance_sheet_df'] = pd.read_csv(uploaded_balance_sheet)
                st.success("Balance Sheet file uploaded!")

                # Filter the Balance Sheet dataframe with its own unique expander
                #st.session_state['balance_sheet_df'] = filter_dataframe(st.session_state['balance_sheet_df'],'Balance_Sheet')
                st.dataframe(st.session_state['balance_sheet_df'])
st.markdown('---')

if st.button("Create Reports"):
    col4, col5 = st.columns([2,1])
    with col4:
        if st.session_state['account_coding_df'] is not None and st.session_state['code_total_df'] is not None:
            # Process the data to create the PNL report
            pnl_report = create_PNL_table(st.session_state['account_coding_df'], st.session_state['code_total_df'])

            # Visualize the report
            visualize_report(pnl_report, "PNL")
        with col5:
            income_row = pnl_report[pnl_report['Category'] == 'INCOME']
            if not income_row.empty:
                st.empty()
                st.empty()
                st.empty()

                # Drop non-numeric columns
                income_data = income_row.drop(columns=['Code', 'Type', 'Category', 'Sub Category', 'Description'])

                # Transpose the data to get months as the index and values as a single column
                income_data = income_data.transpose()

                # Reset the index of the DataFrame so that the months become a column
                income_data.reset_index(inplace=True)

                # Rename the columns for clarity
                income_data.columns = ['Month', 'Value']
                income_data['Month'] = pd.to_datetime(income_data['Month'], format='%B')
                income_data.sort_values('Month', inplace=True)

                # Create a line chart of the income data
                st.markdown(
                    "<h2 style='text-align: center; color:#A7C7E7;'>Monthly Revenue</h2><br><br>",
                    unsafe_allow_html=True)

                st.line_chart(income_data, x='Month', y='Value', color="#AEC6CF", )
            else:
                st.error("No row with 'INCOME' found in the 'Category' column.")

    st.markdown('---')

    col6, col7,col8 = st.columns([1.5,1,1])
    with col6:
        visualize_report(st.session_state['balance_sheet_df'], "BS")
    with col7:
        st.markdown("<h2 style='text-align: center; color:#A7C7E7;'>Current Assets Vs Current liabilaties",
                    unsafe_allow_html=True)
        asset_label = 'רכוש שוטף'
        liability_label = 'התחייבויות שוטפות'
        section_colors = ['#89c2d9', '#A7C7E7']
        create_pie_chart(st.session_state['balance_sheet_df'], asset_label, liability_label, section_colors)
    with col8:
        st.markdown("<h2 style='text-align: center; color:#A7C7E7;'> Currest assets Vs Non current Assets",
                    unsafe_allow_html=True)
        asset_label = 'רכוש שוטף'
        liability_label = 'רכוש קבוע'
        section_colors = ['#A7C7E7', '#89c2d9']
        create_pie_chart(st.session_state['balance_sheet_df'], asset_label, liability_label, section_colors)
    st.markdown('---')

    cf_report,operating_total, investing_total, financing_total = create_cash_flow_statement(st.session_state['account_coding_df'], st.session_state['code_total_df'])
    col9, col10,col11 = st.columns([9,1.5,1])
    
    with col9:
        visualize_report(cf_report, "CF")
    with col10:
        st.markdown("""
        <style>
        .e1f1d6gn3 {
            text-align: left !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h1 style='color: white;'>Summary</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='color: white;'>Summary</h1>", unsafe_allow_html=True)

        st.metric(label="Operating Cash Flow", value="", delta=format_delta(operating_total))
        st.metric(label="Investing Cash Flow", value="", delta=format_delta(investing_total))
        st.metric(label="Financing Cash Flow", value="", delta=format_delta(financing_total))
    with col11:
        st.empty()
        

            
   

    # Display the metrics with the formatted deltas
   










email = st.text_input("Enter email address", key="email_input")

if st.button("Share Report as Google Sheets"):
    if email:  # Check if the email input is not empty
        email_list = [email]  # Convert the email into a single-item list
        st.write(email_list)
        process_spreadsheet("Your_Report", email_list)
        st.success("Report shared successfully!")
    else:
        st.error("Please enter an email address.")

