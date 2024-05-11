import streamlit as st
import os
import pandas as pd
import json
import matplotlib.pyplot as plt
import plotly.express as px

def extract_items(data):
    items_data = []
    for expense_doc in data:
        for line_item_group in expense_doc['ExpenseDocument']['LineItemGroups']:
            for line_item in line_item_group['LineItems']:
                item = None
                cost = None
                for field in line_item['LineItemExpenseFields']:
                    if field['Type']['Text'] == 'ITEM':
                        item = field['ValueDetection']['Text']
                    elif field['Type']['Text'] == 'PRICE':
                        cost_str = ''.join(c for c in field['ValueDetection']['Text'] if c.isdigit() or c == '.')
                        cost = float(cost_str)
                if item is not None and cost is not None:
                    items_data.append({'Item': item, 'Cost': cost})

    # Create a DataFrame
    df = pd.DataFrame(items_data)

    return df

def item_tax_user(df, tax_dict, users):

    # Display DataFrame
    st.subheader("Select Tax and Users:")
    #edited_df = st.data_editor(df, num_rows="dynamic")


    taxes = [f"Tax {i}" for i in range(1, len(tax_dict) + 1)] if tax_dict else []

    with st.expander("Select Tax for Each Item"):
        for index, row in df.iterrows():
            selected_tax = st.radio(f"{row['Item']}: ", [None] + taxes, key=f"{row['Item']}-tax-{index}", horizontal=True)
            df.loc[index, 'Selected Tax'] = selected_tax
            st.write("")  # Add some space between rows

    selected_users_dict = {}
    if 'Selected users' not in df.columns:
        df['Selected users'] = None

    with st.expander("Select users for Each Item"):
        for index, row in df.iterrows():
            selected_users_dict[index] = st.multiselect(f"{row['Item']}: ", users,
                                                            key=f"{row['Item']}-users-{index}",
                                                           default=users)

    for index, selected_users in selected_users_dict.items():
        df.at[index, 'Selected users'] = selected_users



    df = st.data_editor(df, num_rows="dynamic")


    return df


def get_info(data):
    items_data = []
    tax_data = {}
    for expense_doc in data:
        for expense in expense_doc['ExpenseDocument']['SummaryFields']:
            if expense['Type']['Text'] == 'TOTAL':
                items_data.append(("Total", expense['ValueDetection']['Text']))
            elif expense['Type']['Text'] == 'AMOUNT_PAID':
                items_data.append(("Amount Paid", expense['ValueDetection']['Text']))
            elif expense['Type']['Text'] == 'INVOICE_RECEIPT_DATE':
                items_data.append(("Invoice Receipt Date", expense['ValueDetection']['Text']))
            elif expense['Type']['Text'] == 'TAX_PAYER_ID':
                items_data.append(("Tax Payer ID", expense['ValueDetection']['Text']))
            elif expense['Type']['Text'] == 'VENDOR_VAT_NUMBER':
                items_data.append(("Vendor VAT Number", expense['ValueDetection']['Text']))
            elif expense['Type']['Text'] == 'OTHER':
                label_text = expense.get('LabelDetection', {}).get('Text', '')
                value_text = expense['ValueDetection']['Text']
                if '%' in label_text:
                    tax_data[f"Tax {len(tax_data) + 1}"] = label_text
                elif '%' in value_text:
                    tax_data[f"Tax {len(tax_data) + 1}"] = value_text
                if 'CASHIER' in expense.get('LabelDetection', {}).get('Text', ''):
                    items_data.append(("Cashier", expense['ValueDetection']['Text']))
                elif 'TIME' in expense.get('LabelDetection', {}).get('Text', ''):
                    items_data.append(("Time", expense['ValueDetection']['Text']))
                elif 'CASHIER NAME' in expense.get('LabelDetection', {}).get('Text', ''):
                    items_data.append(("Cashier Name", expense['ValueDetection']['Text']))


    return items_data, tax_data

def extract_tax_value(tax_str):
    # Extract numeric part from the string and convert to float
    numeric_part = tax_str.rstrip('%')
    return float(numeric_part)

def print_info(items_data):
    # Display extracted items and costs
    st.subheader("Extracted Information:")
    items_df = pd.DataFrame(items_data, columns=['Item', 'Value'])
    st.table(items_df)
    st.divider()

def take_tax_user(tax_data):
    st.subheader("Tax Information:")
    NoT = st.slider('Number of Taxes', 0, 50, len(tax_data))


    # Display tax information
    if tax_data:

        tax_editable_data = {}
        for i in range(1, NoT + 1):
            tax_label = f"Tax {i}"
            existing_tax_value = tax_data.get(tax_label, '')
            existing_float_value = extract_tax_value(existing_tax_value) if existing_tax_value else None
            tax_value = st.text_input(f"{tax_label} (in %):" , existing_float_value)
            if tax_value:
                tax_float_value = extract_tax_value(tax_value)
                tax_editable_data[tax_label] = tax_float_value

        if len(tax_editable_data) > 0:
            st.table(pd.DataFrame.from_dict(tax_editable_data, orient='index', columns=['Value(%)']))
    else:
        st.write("No tax information found.")


    # --------------------------------------------------------------------------------

    st.subheader("Add User:")
    NoU = st.slider('Number of Users', 1, 50, 1)
    users=[]
    for i in range(1, NoU + 1):
        name = st.text_input(f"Name of user {i}")
        if name in users and (name is not ""):
            st.error("Name already exist.")
        else:
            users.append(name)

    st.divider()
    return tax_editable_data, users

def save_user_spending(user_spending):
    user_spending.to_csv('user_spending.csv', index=False)

# Function to load user spending data from file
def load_user_spending():
    if os.path.exists('user_spending.csv'):
        return pd.read_csv('user_spending.csv')
    else:
        return pd.DataFrame(columns=['user', 'cost'])

def reset_data():
    if os.path.exists('user_spending.csv'):
        os.remove('user_spending.csv')
        st.success("User spending data file deleted successfully!")
    else:
        st.warning("User spending data file does not exist!")

def calculation(dataframe, tax_dict):
    # Convert tax dictionary to pandas Series
    tax_series = pd.Series(tax_dict)


    # Calculate total tax for each item
    dataframe['Total Tax'] = (dataframe['Selected Tax'].map(tax_series) / 100 * dataframe['Cost']).fillna(0)


    # Calculate total cost plus tax for each item
    dataframe['Cost Plus Tax'] = dataframe['Cost'] + dataframe['Total Tax']

    # Split cost based on each user
    user_data = []
    for idx, row in dataframe.iterrows():
        users = row['Selected users']
        total_cost_with_tax = row['Cost Plus Tax']
        cost_per_user = total_cost_with_tax / len(users)
        for user in users:
            user_data.append({'Item': row['Item'], 'user': user, 'cost': cost_per_user})

    user_df = pd.DataFrame(user_data)

    # Calculate total spending per user
    user_spending = user_df.groupby('user')['cost'].sum().reset_index()

    st.write("Tax rate (%):")
    st.write(tax_dict)

    # Visualize the data
    st.write("Item Data:")
    st.write(dataframe)

    st.write("User Spending:")
    st.write(user_spending)

    fig = px.bar(user_spending, x='user', y='cost', labels={'user': 'User', 'cost': 'Spending'},
                 title='User Spending', text='cost')
    fig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                      marker_line_width=1.5, opacity=0.6, textposition='outside')

    fig.update_layout(title_font=dict(size=20), xaxis=dict(title_font=dict(size=14)),
                      yaxis=dict(title_font=dict(size=14)), plot_bgcolor='rgba(0,0,0,0)')

    st.plotly_chart(fig)

    if st.button('Save Data'):
        save_user_spending(user_spending)
        st.success("User spending data saved successfully!")

    if st.button('Reset Data'):
        reset_data()


def main2():
    if os.path.isfile('json_file.json'):
        with open('json_file.json', 'r') as f:
            json_str = f.read()
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError:
            st.error("Error: Failed to decode JSON from 'json_file.json'. Please check the file contents.")

    # ------------------------------------------------------------------------------------------------------------------

        # Extract items and tax information
        items_data, tax_data = get_info(json_data)
        print_info(items_data)
        tax_dict,users = take_tax_user(tax_data)
        df = extract_items(json_data)
        dataframe = item_tax_user(df, tax_dict, users)
        calculation(dataframe, tax_dict)


    else:
        st.error("Error: 'json_file.json' does not exist. Please upload the file first.")




if __name__ == "__main__":
    main2()