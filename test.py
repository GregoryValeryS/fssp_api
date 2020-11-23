import pandas

filename = 'debtors_results'

# файл, с которым будете работать в формате колонок:
# Фамилия   |   Имя   |   Отчество   | Дата рождения | 1 | 2 | 3 | 63 | ... и далее регионы
# Навальный | Алексей | Анатольевич  | 04.06.1976    | 1 | 2 | 3 | 63 | ... .xlsx

result = pandas.read_excel(f'{filename}.xlsx').to_dict(orient='records')

print(result)