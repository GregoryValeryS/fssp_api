import requests
from time import sleep
import pandas

global URL, ACCESS_TOKEN, FILE, TIME_FOR_ANSWER
URL = 'https://api-ip.fssprus.ru/api/v1.0/'  # на случай если сервер API изменится
TOKEN = open(
    'C:/Google Drive/program/matirials_for_fssp_api/fssp_token.txt').read()  # здесь вы указываете свой токен доступа
FILE = 'debtor_list.xlsx'  # файл, с которым будете работать в формате колонок:
# Фамилия   |   Имя   |   Отчество   | Дата рождения | 1 | 2 | 3 | 63 | ... и далее регионы
# Навальный | Алексей | Анатольевич  | 04.06.1976    | 1 | 2 | 3 | 63 | ... .xlsx
TIME_FOR_ANSWER = 42  # иногда сервера fssp требуют на обработку групповго запрса минут 5 (в выходыне особенно)

def status(task: str):
    request = requests.get(f'{URL}status', params={"token": TOKEN, "task": task}).json()


def test():
    """request = requests.get(f'{URL}search/physical', params={
        'token': TOKEN,
        'region': 56,
        'firstname': 'Алексей',
        'secondname': 'Анатольевич',
        'lastname': 'Навальный',
        'birthdate': '04.06.1976',
    }
                           ).json()

    print(request)
    answer = requests.get(f'{URL}result', params={"token": TOKEN, "task": request["response"]["task"]}).json()

    print(answer)"""
    pass


def main():
    # запишем данные из экселя и преобразуем их в список словарей, где каждый словарь - человек
    print(1)
    excel_data_dict = pandas.read_excel(f'{FILE}').to_dict(orient='record')
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

    request_counter = 0  # счётчик запросов

    group_request_params = {"token": TOKEN, "request": []}  # сформируем параметры группового запроса
    subqueries_list = []  # формирую первый пакет на "запрос" мы будем записывать сюда номер человека и регион,
    # по которым сможем в дальнейшем определить, куда записывать полученные данные

    for region in person_keys_list[4:]:  # заполнять таблицу мы будем регион за регионом для каждого согласно списка
        for person_i in range(0, len(excel_data_dict)):  # перебираем людей для этого региона
            if excel_data_dict[person_i][region] != 'нет' and len(excel_data_dict[person_i][region]) < 19:
                # person_i - номер человека в словаре
                # region - регион в который будет запись
                subqueries_list.append([person_i, region])
                print('Групповой запрос [id человека, регион]:', subqueries_list)
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

            # если мы уже набрали 50 подзапросов или мы в конце списка, можно производить запрос
            print(region, int(person_keys_list[-1]))
            print(person_i, len(excel_data_dict) - 1)
            if len(subqueries_list) == max_subqueries_in_group_request or \
                    (region == int(person_keys_list[-1]) and person_i == (len(excel_data_dict) - 1)):
                print('произведём запрос')
                request_counter += 1
                sleep(0.34)
                group_request = requests.post(f'{URL}search/group', json=group_request_params).json()

                print('\nЗапрос', group_request)
                # '044c53e1-8aa5-4f2f-9fa4-f9028d5b00a7' id задачи
                group_request_task_id = group_request["response"]["task"]
                group_request_params["request"] = []

                while True:
                    request_counter += 1
                    print(f'Дадим время на обратку запроса - {TIME_FOR_ANSWER} сек.')
                    sleep(TIME_FOR_ANSWER)  # иногда - минута, иногда несколько секунд
                    answer = requests.get(f'{URL}result', params={"token": TOKEN, "task": group_request_task_id}).json()
                    print('Задача ещё исполняется')
                    if answer["response"]["task_end"] is not None:
                        print('Задача выполнена')
                        break

                print('\nОтвет', answer)
                number_of_person = 0
                # начинаем перечислять результаты запросов (по результату на человека (на подзапрос))
                for person_result in answer["response"]["result"]:
                    writing_data = ''
                    i = 0  # инициация нумерации (результатов на человека может быть несколько)
                    if len(person_result["result"]) == 0:
                        writing_data = 'нет'
                    else:
                        for result in person_result["result"]:
                            i += 1
                            writing_data += str(i) + '. '
                            for key in result:
                                writing_data += result[key] + ' '

                    print('\nЗаписано в человека', number_of_person, writing_data)
                    # запишем полученный ответ(ы)
                    # writing_data subqueries_list[number_of_person][0] - номер человека в словаре
                    # [subqueries_list[number_of_person][1]] - регион в который будет запись
                    excel_data_dict[subqueries_list[number_of_person][0]][
                        subqueries_list[number_of_person][1]] = writing_data
                    number_of_person += 1

                subqueries_list = []
                # преобразовываем обратно в data frame
                data_frame = pandas.DataFrame.from_dict(excel_data_dict)
                # перезаписываем файл в excel
                data_frame.to_excel(f'{FILE}', index=False)

    print('Работа с файлом завершена')


if __name__ == '__main__':
    main()