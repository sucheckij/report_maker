import numpy as np
import pandas as pd
import openpyxl

df_org = pd.read_excel('workitems_with_description.xlsx')

df = df_org.copy()

print(df)
for index, row in df_org.iterrows():
    if df_org.at[index,'Type'] == 'Heading':
        df = df.drop(index)
print(df)
df = df.reset_index(drop=True)


print(df.to_string())

# przejscie po indexach i ID
for index, value in df['ID'].items():
    print(f"Wiersz {index}: {value}")

# sprawdzenie czy wartosc wiersza znajduje sie w kolumnie
checking_value = 'DSS-2015'
if_present = df['ID'].isin([checking_value]).any()
print(f"Value {checking_value} is in dataframe: {if_present}")

# zwrócenie indeksu dla wybranego elementu
checking_element = 'DSS-2015'
for index, value in df['ID'].items():
    if value == checking_element:
        idx = index
        break
print(f"Checked idx:{idx}")


# wypelnienie NaN wartosciami wlasciwych IDs
current_ID = df.at[0,'ID']

for index, row in df.iterrows():
    print(row.ID)
    # print(row.ID)
    # print(type(row.ID))
    if pd.isna(df.at[index,'ID']):
        df.at[index,'ID'] = current_ID
    else:
        current_ID = row.ID

# wypelnienie NaN wartosciami wlasciwych Step_number
current_ID = df.at[0,'ID']
i = 1
for index, row in df.iterrows():
    if df.at[index,'ID'] != current_ID:
        i = 1
        current_ID = row.ID

    df.at[index,'#'] = i
    i+=1

# wypelnienie NaN wartosciami wlasciwych Title
for index, row in df.iterrows():

    if pd.isna(df.at[index,'Title']) and index !=0:
        df.at[index, 'Title'] = df.at[index-1, 'Title']

df = df.drop(columns=['_polarion'])
print(df.to_string())

df.to_excel("new_file.xlsx", engine='openpyxl', index=True)


df_new = pd.read_excel('new_file.xlsx')
value_counts  = df_new['ID'].value_counts()['DSS-2015']
print(f"Liczba wystąpień w kolumnie: {value_counts}")

# print("Send frame to read the register:\r\n [\r\n Slave ID: 0x01      \r\n Function code: 0x10 \r\n Address: first NA_Register from Space 2\r\n Quantity: 0x0003\r\n Byte Count: 0x06\r\n Value: 6 bytes  \r\n ]\r\n")
# print("Response frame should be:\r\n [\r\n Slave ID: 0x01\r\n Function code: 0x03\r\n Byte count: 0x02\r\n Register value: : 2 bytes \r\n")


# How to handle exceptions

# def handle_exceptions(f: Callable, exception) -> Callable:
#     def wrapper(*args, **kwargs):
#         try:
#             return f(*args, **kwargs)
#         except Exception as e:
#             if exception == Exceptions.WARNING.value:
#                 print(f'WARNING: {e}')
#             elif exception == Exceptions.ERROR.value:
#                 raise e
#             raise e
#     return wrapper
