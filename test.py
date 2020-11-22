import pandas
region_excel_filename = 'debtors'

# файл, с которым будете работать в формате колонок:
# Фамилия   |   Имя   |   Отчество   | Дата рождения | 1 | 2 | 3 | 63 | ... и далее регионы
# Навальный | Алексей | Анатольевич  | 04.06.1976    | 1 | 2 | 3 | 63 | ... .xlsx

region_dict = pandas.read_excel(f'{region_excel_filename}.xlsx').to_dict(orient='records')

print(region_dict)