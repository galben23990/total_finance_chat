import chardet
import pandas as pd
import datetime
import os
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import streamlit as st
import os
import json
import pygsheets
import pandas as pd
from google.cloud import bigquery
import gspread
from gspread_formatting import *


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']


def append_category_totals(monthly_pnl_table):
    all_dataframes = []
    unique_categories = monthly_pnl_table['Category'].unique()

    for category in unique_categories:
        category_df = monthly_pnl_table[monthly_pnl_table['Category'] == category]

        total_row = category_df.sum(numeric_only=True)
        total_row['Code'] = f'{category} Total'
        total_row['Category'] = category
        total_row['SubCategory'] = ''
        total_row['Description'] = ''
        total_row['Code_Name'] = ''

        category_df = category_df.append(total_row, ignore_index=True)
        all_dataframes.append(category_df)

    return pd.concat(all_dataframes).reset_index(drop=True)


def reorder_columns(dataframe, new_order):
    # Removing duplicated columns in new_order list
    new_order = list(dict.fromkeys(new_order))

    # Checking if all columns in new_order are present in the dataframe
    for column in new_order:
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found in the dataframe.")

    # Reordering the columns
    dataframe = dataframe[new_order]

    return dataframe


def convert_excel_date(serial_date, row_index, row):
    try:
        # Excel’s epoch is 1900-01-01, but there's a bug where Excel thinks 1900 was a leap year, hence the -2
        return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(serial_date))).strftime('%Y-%m')
    except ValueError as e:
        print(f"No date was found in row {row_index}: {row}. Error: {e}")
        return None


# Detect the encoding for each file

def get_data(account_coding, code_total):

    account_coding_encoding = detect_encoding(account_coding)
    code_total_encoding = detect_encoding(code_total)

    account_coding = pd.read_csv(account_coding, encoding=account_coding_encoding)
    code_total = pd.read_csv(code_total, encoding=code_total_encoding)
    return account_coding, code_total


def create_PNL_table(account_coding, code_total):
    print("bug?")

    split_values = account_coding['סעיף מאזן בוחן'].str.split(".", expand=True)
    account_coding.insert(1, 'Code_Number', split_values[0])
    merged_data = match_total_code_to_merge(account_coding, code_total)
    merged_data_filter = merged_data[merged_data['report'] == 'PNL']

    merged_data_filter['Net'] = merged_data_filter['זכות'] - merged_data_filter['חובה']
    merged_data_filter['Year'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y').dt.year
    merged_data_filter['Month'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y').dt.month

    # Group by Account and YearMonth, then sum and keep the necessary values
    aggregated_data = merged_data_filter.groupby(['חשבון', 'Year', 'Month']).agg(
        Description=('Description', 'first'),
        תיאור=('תאור', 'first'),
        סעיף_מאזן_בוחן=('סעיף מאזן בוחן', 'first'),
        code_name=('code_name', 'first'),
        Code_Number=('Code_Number', 'first'),
        Category=('Category', 'first'),
        SubCategory=('SubCategory', 'first'),
        חובה_בשקלים=('חובה', 'sum'),
        זכות_בשקלים=('זכות', 'sum'),
        Net=('Net', 'sum')
        # keeping the first value in each group
    ).reset_index()

    # dates are coloumns , rows are arragened by Code_Number=('Code_Number', 'first') sorted by Code_Number creata a data frame in this order called monthly pnl table
    monthly_pnl_table = pd.pivot_table(aggregated_data,
                                       values=['Net'],
                                       index=['Code_Number', 'Category', "SubCategory", 'Description', 'code_name'],
                                       columns=['Month'],
                                       aggfunc={'Net': 'sum'},
                                       fill_value=0)

    # Resetting index for a cleaner look

    monthly_pnl_table.reset_index(inplace=True)

    # Sorting the table by Code Number
    monthly_pnl_table.sort_values(by='Code_Number', inplace=True)

    # Renaming index columns with more meaningful names
    new_column_names = {
        'Code_Number': 'Code',
        'Category': 'Category',
        'SubCategory': 'SubCategory',
        'Description': 'Descreaption',
        'code_name': 'Code_Name'
    }

    monthly_pnl_table.rename(columns=new_column_names, inplace=False)

    month_mapping = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    # Applying the month names to the respective columns
    project_directory = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(project_directory, "monthly_pnl_table.csv")
    monthly_pnl_table.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
    # Other cod
    monthly_pnl_table.columns = [month_mapping.get(col, col) for col in monthly_pnl_table.columns.get_level_values(1)]
    current_columns = list(monthly_pnl_table.columns)

    # Update the first four column names
    current_columns[:5] = ['Code', 'Type', 'Category', 'Sub Category', 'Description']

    # Assign the updated column names back to the DataFrame
    monthly_pnl_table.columns = current_columns

    csv_file_path = os.path.join("C:\\Users\\user\\Downloads", "monthly_pnl_table.csv")
    monthly_pnl_table.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

    return monthly_pnl_table


def match_total_code_to_merge(account_coding, code_total):
    account_coding['Code_Number'] = account_coding['Code_Number'].astype(float)
    code_total['code'] = code_total['code'].astype(float)
    split_values = account_coding['סעיף מאזן בוחן'].str.split(".", expand=True)
    account_coding.insert(1,'code_name', split_values[1])

    print("bug3?")

    merged_data = pd.merge(account_coding, code_total[
        ['code', 'Description', 'code_group_index', 'code_group', 'SubCategory_code', 'SubCategory', 'Category',
         'report']], left_on='Code_Number', right_on='code', how='left')
    return merged_data


def create_BS_table(account_coding, code_total, acc):
    split_values = account_coding['סעיף מאזן בוחן'].str.split(".", expand=True)
    account_coding.insert(1, 'Code_Number', split_values[0])
    merged_data = match_total_code_to_merge(account_coding, code_total)
    merged_data_filter = merged_data[merged_data['report'] == 'BS']

    merged_data_filter['Net'] = merged_data_filter['חובה'] - merged_data_filter['זכות']
    merged_data_filter['Year'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y',
                                                errors='coerce').dt.year
    merged_data_filter['Month'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y',
                                                 errors='coerce').dt.month
    merged_data_filter.dropna(subset=['Year', 'Month'], inplace=True)

    # Group by Account and YearMonth, then sum and keep the necessary values
    aggregated_data = merged_data_filter.groupby(['חשבון', 'Year', 'Month']).agg(
        Description=('Description', 'first'),
        תיאור=('תאור', 'first'),
        סעיף_מאזן_בוחן=('סעיף מאזן בוחן', 'first'),
        code_name=('code_name', 'first'),
        Code_Number=('Code_Number', 'first'),
        Category=('Category', 'first'),
        SubCategory=('SubCategory', 'first'),
        חובה_בשקלים=('חובה', 'sum'),
        זכות_בשקלים=('זכות', 'sum'),
        Net=('Net', 'sum')
    ).reset_index()

    # Pivot table to rearrange data
    monthly_bs_table = pd.pivot_table(aggregated_data,
                                      values=['Net'],
                                      index=['Code_Number', 'Category', "SubCategory", 'Description', 'code_name'],
                                      columns=['Month'],
                                      aggfunc={'Net': 'sum'},
                                      fill_value=0)

    # Resetting index for a cleaner look
    monthly_bs_table.columns.set_levels(monthly_bs_table.columns.levels[1].astype(int), level='Month', inplace=True)

    # Now sort the 'Month' level
    months_present = monthly_bs_table.columns.levels[1].sort_values()

    for i, month in enumerate(months_present):
        if i > 0:
            monthly_bs_table[('Net', month)] += monthly_bs_table[('Net', months_present[i - 1])]

    # Flatten the MultiIndex columns after mapping
    monthly_bs_table.columns = ['_'.join(map(str, col)).strip() for col in monthly_bs_table.columns.values]

    # Rename the column headers to more meaningful names and apply month names
    month_mapping = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    # Update the column names with month names and meaningful index names
    new_column_names = {
        'Code_Number': 'Code',
        'Category_Category': 'Category',
        'SubCategory_SubCategory': 'SubCategory',
        'Description_Description': 'Description',
        'code_name_code_name': 'Code_Name'
    }

    for old_name, new_name in new_column_names.items():
        if old_name in monthly_bs_table.columns:
            monthly_bs_table.rename(columns={old_name: new_name}, inplace=True)

    # Rename the months in columns
    monthly_bs_table.columns = [month_mapping.get(int(col.split('_')[-1]), col) if col.split('_')[-1].isdigit() else col
                                for col in monthly_bs_table.columns]

    # Sorting the table by Code Number

    monthly_bs_table.sort_values(by='Code_Number', inplace=True)

    # Save to CSV file
    csv_file_path = os.path.join("C:\\Users\\user\\Downloads", "monthly_bs_table.csv")
    monthly_bs_table.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

    return monthly_bs_table


def create_pie_chart(df, asset_label, liability_label, colors, title='Pie Chart', currency_col='סכום בשקלים'):
    """
    Creates a pie chart for the current assets vs current liabilities from a DataFrame.

    Parameters:
    - df: DataFrame containing the data.
    - asset_label: The label in the DataFrame that identifies current assets.
    - liability_label: The label in the DataFrame that identifies current liabilities.
    - colors: A list of colors for the pie chart sections.
    - title: The title of the pie chart.
    - currency_col: The name of the column containing the currency values.
    """
    # Compute the sums for assets and liabilities
    assets_sum = df[df['כותרת משנה;'] == asset_label][currency_col].sum()
    liabilities_sum = df[df['כותרת משנה;'] == liability_label][currency_col].sum()

    # Data and labels for the pie chart
    data = [assets_sum, liabilities_sum]
    labels = [asset_label, liability_label]

    # Correct the labels for Hebrew text direction
    labels = [get_display(arabic_reshaper.reshape(label)) for label in labels]
    title = get_display(arabic_reshaper.reshape(title))

    # Create the pie chart
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Set a font that supports Hebrew characters
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Use Streamlit's pyplot function to display the figure
    st.pyplot(fig)


def set_border(worksheet, start, end, border_style):
    border = pygsheets.Border(position='GRID',
                              color={'red': 0, 'green': 0, 'blue': 0, 'alpha': 1},
                              width=2, style=border_style)
    worksheet.set_borders(start, end, border)


def color_row(worksheet, row_number, color, table_length):
    for col_index in range(1, table_length + 1):  # Loop through all columns in the row
        cell_label = pygsheets.utils.format_addr((row_number, col_index))  # Format the cell label
        worksheet.cell(cell_label).color = color  # Set cell color


def process_spreadsheet(df, users_to_share):
    # Load service account key from environment variable which contains the JSON key
    service_account_info = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT"))
    key_dict = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
    client = bigquery.Client.from_service_account_info(key_dict)
    gc = pygsheets.authorize(service_account_env_var='FIREBASE_SERVICE_ACCOUNT')

    # Create a new Google Sheets and set the dataframe
    spreadsheet = gc.create('New Spreadsheet from DataFrame')
    worksheet = spreadsheet.sheet1
    worksheet.set_dataframe(df, (1, 1))

    # Find the last column with a value in row 1
    row_values = worksheet.get_row(1, include_tailing_empty=False)
    table_length = len(row_values)

    for email in users_to_share:
        spreadsheet.share(email, role='writer', type='user')

    # Share the spreadsheet with a user
    spreadsheet.share('gal@finityx.com', role='writer', type='user')
    cells_with_income = worksheet.find("INCOME")
    cells_with_operating_costs = worksheet.find("OPERATING COSTS")
    cells_with_financing_expenses = worksheet.find("FINANCING EXPENSES")
    # Set to keep track of rows that have been processed
    processed_rows = set()

    for cell in cells_with_income:
        row_number = cell.row  # Get the row number for the cell with "INCOME"
        if row_number not in processed_rows:  # Check if the row has been processed
            color_row(worksheet, row_number, (0.75, 0.75, 1), table_length)  # RGB for light blue color
            processed_rows.add(row_number)  # Mark the row as processed

    # Loop through each cell that contains "OPERATING COSTS"
    for cell in cells_with_operating_costs:
        row_number = cell.row  # Get the row number for the cell with "OPERATING COSTS"
        if row_number not in processed_rows:  # Check if the row has been processed
            color_row(worksheet, row_number, (1, 0.75, 0.75), table_length)  # RGB for light red color
            processed_rows.add(row_number)  # Mark the row as processed

    for cell in cells_with_financing_expenses:
        row_number = cell.row  # Get the row number for the cell with "OPERATING COSTS"
        if row_number not in processed_rows:  # Check if the row has been processed
            color_row(worksheet, row_number, (0, 0, 0.75), table_length)  # RGB for light red color
            processed_rows.add(row_number)  # Mark the row as processed



def create_cash_flow_statement(account_coding, code_total):

    account_coding['Code_Number'] = account_coding['Code_Number'].astype(float)
    code_total['code'] = code_total['code'].astype(float)
    split_values = account_coding['סעיף מאזן בוחן'].str.split(".", expand=True)

    merged_data = pd.merge(account_coding, code_total[
        ['code', 'Description', 'code_group_index', 'code_group', 'SubCategory_code', 'SubCategory', 'Category',
         'report']], left_on='Code_Number', right_on='code', how='left')

    merged_data_filter = merged_data[merged_data['report'] == 'BS']

    merged_data_filter['Net'] = merged_data_filter['חובה']-merged_data_filter['זכות']
    merged_data_filter['Year'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y', errors='coerce').dt.year
    merged_data_filter['Month'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y', errors='coerce').dt.month
    merged_data_filter = merged_data_filter.sort_values(['חשבון', 'Year', 'Month'])
    # Group by account and year and compute cumulative sum of 'Net' within each group
    merged_data_filter['Cumulative_Net'] = merged_data_filter.groupby(['חשבון', 'Year'])['Net'].cumsum()

    # Group by account and year and compute cumulative sum of 'Net' within each group
    merged_data_filter['Cumulative_Net'] = merged_data_filter.groupby(['חשבון', 'Year'])['Net'].cumsum()

    aggregated_data = merged_data_filter.groupby(['חשבון', 'Year', 'Month']).agg(
        Description=('Description', 'first'),
        תיאור=('תאור', 'first'),
        סעיף_מאזן_בוחן=('סעיף מאזן בוחן', 'first'),
        code_name=('code_name', 'first'),
        Code_Number=('Code_Number', 'first'),
        Category=('Category', 'first'),
        SubCategory=('SubCategory', 'first'),
        חובה_בשקלים=('חובה', 'sum'),
        זכות_בשקלים=('זכות', 'sum'),
        Net=('Net', 'sum'),
        cumulative_net=('Cumulative_Net', 'last'),

        יתרת_פתיחה=('יתרת פתיחה', 'max')  # Assuming you want the max opening balance if there are multiple per account
    ).reset_index()

    # Add the opening balance to the Net sum
    aggregated_data['Net_including_opening'] = aggregated_data['cumulative_net'] + aggregated_data['יתרת_פתיחה']

    monthly_cf_table = pd.pivot_table(aggregated_data,
                                      values='Net_including_opening',
                                      index=['Code_Number', 'Category', "SubCategory", 'Description', 'code_name'],
                                      columns='Month',
                                      aggfunc=sum,
                                      fill_value=0).reset_index()



    month_mapping = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }
    
    monthly_cf_table.columns = [month_mapping.get(col, col) for col in monthly_cf_table.columns]
    new_df = monthly_cf_table[['Code_Number', 'code_name', 'August', 'September']].copy()
# Ensure that Code_Number is of the same type in both dataframes to avoid merge issues.
    new_df['Code_Number'] = new_df['Code_Number'].astype(float)
    code_total['code'] = code_total['code'].astype(float)

    # Merge the new dataframe with code_total to bring in the cash flow descriptions.
    # The merge is done on 'Code_Number' and 'code', ensuring that they are of the same data type.
    new_df = new_df.merge(code_total[['code', 'Description', 'Operating Activities', 'Investing Activities', 'Financing Activities']],
                        left_on='Code_Number', right_on='code', how='left')

    # Assuming the 'Description' column indicates where the 'Difference' should be allocated:
    # Here we would allocate the difference based on the description. 
    # This assumes you have a predefined logic that you can use to allocate based on the descriptions.

    # For demonstration, let's assume if the description contains certain keywords, we allocate to that category.
    # We initialize the columns with 0 first.
    new_df['Operating Activities'] = 0
    new_df['Investing Activities'] = 0
    new_df['Financing Activities'] = 0

    # A simple allocation logic based on keywords in the description.
    # You might have more complex logic depending on your actual data.
   
def create_cash_flow_statement(account_coding, code_total):

    account_coding['Code_Number'] = account_coding['Code_Number'].astype(float)
    code_total['code'] = code_total['code'].astype(float)
    split_values = account_coding['סעיף מאזן בוחן'].str.split(".", expand=True)

    merged_data = pd.merge(account_coding, code_total[
        ['code', 'Description', 'code_group_index', 'code_group', 'SubCategory_code', 'SubCategory', 'Category',
         'report']], left_on='Code_Number', right_on='code', how='left')

    merged_data_filter = merged_data[merged_data['report'] == 'BS']

    merged_data_filter['Net'] = merged_data_filter['חובה']-merged_data_filter['זכות']
    merged_data_filter['Year'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y', errors='coerce').dt.year
    merged_data_filter['Month'] = pd.to_datetime(merged_data_filter['תאריך למאזן'], format='%d/%m/%Y', errors='coerce').dt.month
    merged_data_filter = merged_data_filter.sort_values(['חשבון', 'Year', 'Month'])
    # Group by account and year and compute cumulative sum of 'Net' within each group
    merged_data_filter['Cumulative_Net'] = merged_data_filter.groupby(['חשבון', 'Year'])['Net'].cumsum()

    # Group by account and year and compute cumulative sum of 'Net' within each group
    merged_data_filter['Cumulative_Net'] = merged_data_filter.groupby(['חשבון', 'Year'])['Net'].cumsum()

    aggregated_data = merged_data_filter.groupby(['חשבון', 'Year', 'Month']).agg(
        Description=('Description', 'first'),
        תיאור=('תאור', 'first'),
        סעיף_מאזן_בוחן=('סעיף מאזן בוחן', 'first'),
        code_name=('code_name', 'first'),
        Code_Number=('Code_Number', 'first'),
        Category=('Category', 'first'),
        SubCategory=('SubCategory', 'first'),
        חובה_בשקלים=('חובה', 'sum'),
        זכות_בשקלים=('זכות', 'sum'),
        Net=('Net', 'sum'),
        cumulative_net=('Cumulative_Net', 'last'),

        יתרת_פתיחה=('יתרת פתיחה', 'max')  # Assuming you want the max opening balance if there are multiple per account
    ).reset_index()

    # Add the opening balance to the Net sum
    aggregated_data['Net_including_opening'] = aggregated_data['cumulative_net'] + aggregated_data['יתרת_פתיחה']

    monthly_cf_table = pd.pivot_table(aggregated_data,
                                      values='Net_including_opening',
                                      index=['Code_Number', 'Category', "SubCategory", 'Description', 'code_name'],
                                      columns='Month',
                                      aggfunc=sum,
                                      fill_value=0).reset_index()



    month_mapping = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }
    
    monthly_cf_table.columns = [month_mapping.get(col, col) for col in monthly_cf_table.columns]
    new_df = monthly_cf_table[['Code_Number', 'code_name', 'August', 'September']].copy()
# Ensure that Code_Number is of the same type in both dataframes to avoid merge issues.
    new_df['Code_Number'] = new_df['Code_Number'].astype(float)
    code_total['code'] = code_total['code'].astype(float)

    # Merge the new dataframe with code_total to bring in the cash flow descriptions.
    # The merge is done on 'Code_Number' and 'code', ensuring that they are of the same data type.
    new_df = new_df.merge(code_total[['code', 'cashflow description']],
                        left_on='Code_Number', right_on='code', how='left')

    # Assuming the 'Description' column indicates where the 'Difference' should be allocated:
    # Here we would allocate the difference based on the description. 
    # This assumes you have a predefined logic that you can use to allocate based on the descriptions.
    # Initialize columns for cash flow activities
    new_df['Operating Activities'] = 0
    new_df['Investing Activities'] = 0
    new_df['Financing Activities'] = 0  # Ad
    # For demonstration, let's assume if the description contains certain keywords, we allocate to that category.
    # We initialize the columns with 0 first.
    for index, row in new_df.iterrows():
        description = row['cashflow description']

        # Your categorization logic here
        if 'operating' in description.lower():
            new_df.at[index, 'Operating Activities'] = row['September'] -row['August']
        elif 'investing' in description.lower():
            new_df.at[index, 'Investing Activities'] = row['September'] -row['August']
        elif 'financing' in description.lower():
            new_df.at[index, 'Financing Activities'] = row['September'] -row['August']
        

# You can now drop the duplicate 'code' column after merging. This line should only be present once.
    new_df.drop('code', axis=1, inplace=True)
    final_df = new_df[['Code_Number', 'code_name', 'cashflow description','August', 'Operating Activities', 'Investing Activities','Financing Activities', 'September']]
    
    operating_total = final_df['Operating Activities'].sum()
    investing_total = final_df['Investing Activities'].sum()
    financing_total = final_df['Financing Activities'].sum()
    final_df_without_first_two_columns = final_df.iloc[:, 1:]

    
    return final_df_without_first_two_columns, operating_total, investing_total, financing_total



def main(account_coding, code_total):
    account_coding, code_total = get_data(account_coding, code_total)
    monthly_pnl_table = process_spreadsheet(df, users_to_share)
    return monthly_pnl_table



