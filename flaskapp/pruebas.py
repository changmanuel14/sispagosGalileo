import unicodedata

string_1 = 'función'
string_2 = "Función "

print(unicodedata.normalize('NFKD', string_1).encode('ASCII', 'ignore').strip().lower() == unicodedata.normalize('NFKD', string_2).encode('ASCII', 'ignore').strip().lower())