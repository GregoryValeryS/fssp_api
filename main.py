import requests
import json
from time import sleep
import pandas

global URL, ACCESS_TOKEN
URL = 'https://api-ip.fssprus.ru/api/v1.0/'  # на случай если сервер API изменится
TOKEN = open(
    'C:/Google Drive/program/matirials_for_fssp_api/fssp_token.txt').read()  # здесь вы указываете свой токен доступа


def status(task: str):
    request = requests.get(f'{URL}status', params={"token": TOKEN, "task": task}).json()


def test():
    request = requests.get(f'{URL}search/physical', params={
        'token': TOKEN,
        'region': 56,
        'firstname': 'Сергей',
        'secondname': 'Александрович',
        'lastname': 'СПИРИДОНОВ',
        'birthdate': '04.09.1983',
    }
                           ).json()

    print(request)
    answer = requests.get(f'{URL}result', params={"token": TOKEN, "task": request["response"]["task"]}).json()

    print(answer)


def main():
    # запишем данные из экселя и преобразуем их в список словарей, где каждый словарь - человек
    excel_data_dict = pandas.read_excel(f'C:/Google Drive/program/matirials_for_fssp_api/test.xlsx').to_dict(
        orient='record')
    # преобразуем формат даты в текст, удалим лишние пробелы, заменим 'nan' на пустые строки
    person_keys_list = list(excel_data_dict[0].keys())

    for person in excel_data_dict:

        for fio in person_keys_list[0:3]:  # первые 3 кюча - Фамилия, Имя, Отчество. Удалим пробелы
            person[fio] = person[fio].replace(' ', '')

        # дату рождения необходимо перевернуть из формата даты, если год стоит первым
        date_list = str(person['Дата рождения'])[0:10].replace('-', '.').replace(' ', '').split('.')
        if len(date_list[0]) == 4:
            person['Дата рождения'] = str(date_list[2] + '.' + date_list[1] + '.' + date_list[0])
        else:
            person['Дата рождения'] = str(date_list[0] + '.' + date_list[1] + '.' + date_list[2])

        for region in person_keys_list[4:]:  # все ключи после 4 - номера регионов, зачищаем значения
            if str(person[region]) == 'nan':
                person[region] = ''

    max_subqueries_in_group_request = 50  # Максимальное число подзапросов в групповом запросе
    max_single_requests_per_hour = 100  # Максимальное число одиночных запросов в час
    max_single_requests_per_day = 1000  # Максимальное число одиночных запросов в сутки

    subqueries_counter = 0  # счётчик подзапросов
    request_counter = 0  # счётчик запросов

    group_request_params = {"token": TOKEN, "request": []}  # сформируем параметры группового запроса
    to_write_list = []  # формирую первый пакет на "запрос" мы будем записывать сюда номер человека и регион,
    # по которым сможем в дальнейшем определить, куда записывать полученные данные

    for region in person_keys_list[4:]:  # заполнять таблицу мы будем регион за регионом для каждого согласно списка
        for person_i in range(0, len(excel_data_dict) - 1):  # перебираем людей для этого региона
            # если мы уже набрали 50 подзапросов, можно производить запрос
            if subqueries_counter == 23:
                request_counter += 1
                sleep(0.34)
                group_request = requests.post(f'{URL}search/group', json=group_request_params).json()
                group_request_task_id = group_request["response"]["task"]
                group_request_params["request"] = []

                while True:
                    request_counter += 1
                    sleep(4.2)  # кто знает, сколько серверу понадобится для обработки запроса?
                    answer = requests.get(f'{URL}result', params={"token": TOKEN, "task": group_request_task_id}).json()
                    if answer["response"]["task_end"] is not None:
                        break
                print(answer)
                print('')

                number_of_person_write_list = 0
                for person_result in answer["response"]["result"]:
                    writing_data = ''
                    i = 0
                    for result in person_result["result"]:
                        if len(result) > 2:
                            i += 1
                            writing_data += str(i) + '. '
                            for key in result:
                                writing_data += result[key] + ' '
                        else:
                            writing_data = 'нет'

                    excel_data_dict[to_write_list[number_of_person_write_list][0]][to_write_list[number_of_person_write_list][1]] = writing_data
                    number_of_person_write_list += 1

                to_write_list = []
                subqueries_counter = 0
                print(excel_data_dict)
                print('')

            if excel_data_dict[person_i][region] != 'нет':
                subqueries_counter += 1
                to_write_list.append([person_i, region])
                group_request_params["request"].append(
                    {
                        "type": 1,
                        "params": {
                            "firstname": excel_data_dict[person_i]['Имя'],
                            "lastname": excel_data_dict[person_i]['Фамилия'],
                            "secondname": excel_data_dict[person_i]['Отчество'],
                            "region": region,
                            "birthdate": excel_data_dict[person_i]['Дата рождения']
                        }
                    }
                )




if __name__ == '__main__':
    main()
