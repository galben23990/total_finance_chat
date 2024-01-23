import pandas as pd
import os

# Set the directory where your files are located
dir_path = "C:/Users/user/Desktop/Total/user_way"

# Create a list for the months in order from Jan 2022 to Sep 2023
months = ["jan22", "feb22", "mar22", "apr22", "may22", "jun22", "jul22", "aug22", "sep22",
          "oct22", "nov22", "dec22", "jan23", "feb23", "mar23", "apr23", "may23", "jun23",
          "jul23", "aug23", "sep23"]

# Initialize an empty DataFrame to hold all the monthly data
monthly_table = pd.DataFrame()

# Iterate over each month and load the corresponding file
for month in months:
    file_path = os.path.join(dir_path, f"{month}.csv")
    if os.path.exists(file_path):
        # Read the CSV file into a DataFrame
        monthly_data = pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        # You may want to add a date or month column to identify the records from each file
        monthly_data['Month'] = month
        
        # Append the monthly data to the main DataFrame
        monthly_table = monthly_table.append(monthly_data, ignore_index=True)

# Once all files are processed, you can inspect the combined DataFrame
print(monthly_table.head())

# If you want to save the combined table to a new CSV file
monthly_table.to_csv("C:/Users/user/Desktop/Total/combined_balance_sheet.csv", sep=';', index=False, encoding='utf-8')
