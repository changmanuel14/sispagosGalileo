import gspread
from oauth2client.service_account import ServiceAccountCredentials


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\USUARIO\Documents\siscaja\flaskapp\client_secret.json", scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Prueba Python").sheet1

row = [5, "Juan Manuel", "J"]
index = 2
sheet.insert_row(row, index)

# Extract and print all of the values
datos = sheet.get_all_values()
print(datos)