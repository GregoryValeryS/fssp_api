import requests
from time import sleep
import pandas
from sys import argv as sys_argv, exit as sys_exit
from PyQt5 import QtWidgets
from ui_window_main import Ui_MainWindow

global URL, TOKENS, TIME_FOR_ANSWER
URL = 'https://api-ip.fssprus.ru/api/v1.0/'  # на случай если сервер API изменится
# здесь вы указываете свой токен доступа
TOKENS = open('C:/Google Drive/program/matirials_for_fssp_api/fssp_token.txt').read().split('\n')
TIME_FOR_ANSWER = 42  # иногда сервера fssp требуют на обработку групповго запрса минут 5 (в выходыне особенно)


def status(task: str):
    request = requests.get(f'{URL}status', params={"token": TOKEN, "task": task}).json()


def search():
    push_request('search', TOKENS)


def update():
    push_request('update', TOKENS)


def push_request(search_or_update: str, tokens: list):
    # запишем данные из экселя и преобразуем их в список словарей
    region_excel_filename = main_menu.lineEdit_region_filename.text()
    # файл, с которым будете работать в формате колонок:
    # Фамилия   |   Имя   |   Отчество   | Дата рождения | 1 | 2 | 3 | 63 | ... и далее регионы
    # Навальный | Алексей | Анатольевич  | 04.06.1976    | 1 | 2 | 3 | 63 | ... .xlsx
    region_dict = pandas.read_excel(f'{region_excel_filename}.xlsx').to_dict(orient='records')

    # сгенерируем метаданные, ключи и все id
    region_keys_list = list(region_dict[0].keys())
    region_id_list = range(len(region_dict))
    regions = region_keys_list[4:]

    # преобразуем формат даты в текст, удалим лишние пробелы, заменим 'nan' на пустые строки
    for key in region_keys_list:
        for i in region_id_list:
            region_dict[i][key] = str(region_dict[i][key]).replace(' ', '')

            if key == 'lastname' or key == 'firstname' or key == 'secondname':
                region_dict[i][key] = region_dict[i][key].title()

            if type(key) is int:
                if region_dict[i][key] == 'x':
                    continue
                else:
                    region_dict[i][key] = ''

            if key == 'birthdate':
                birthdate_in_list = region_dict[i][key][0:10].replace('-', '.').split('.')
                # если в начале стоит год
                if len(birthdate_in_list[0]) == 4:  # переносим его в конец
                    region_dict[i][key] = str(f'{birthdate_in_list[2]}.{birthdate_in_list[1]}.{birthdate_in_list[0]}')
                # если в конце стоит год
                elif len(birthdate_in_list[2]) == 4:  # оставляем всё, как есть
                    region_dict[i][key] = str(f'{birthdate_in_list[0]}.{birthdate_in_list[1]}.{birthdate_in_list[2]}')
                # если в начале год из 2х символов и в конце дата
                elif int(birthdate_in_list[0]) > 31 and len(birthdate_in_list[0]) == 2 and int(
                        birthdate_in_list[2]) <= 31:
                    # переносим год назад, добавляем 19
                    region_dict[i][key] = str(f'{birthdate_in_list[2]}.{birthdate_in_list[1]}.19{birthdate_in_list[0]}')
                # если в конце год из 2 символов и в начале число
                elif int(birthdate_in_list[2]) > 31 and len(birthdate_in_list[2]) == 2 and int(
                        birthdate_in_list[0]) <= 31:
                    # отсавляем порядок тот же, добавляем 19 в году
                    region_dict[i][key] = str(f'{birthdate_in_list[0]}.{birthdate_in_list[1]}.19{birthdate_in_list[2]}')
                # если в начале и в конце возможны год и дата
                elif int(birthdate_in_list[0]) <= 31 and int(birthdate_in_list[2]) <= 31:
                    # надо решить, что поставить перед годом, 20 ил 19
                    if int(birthdate_in_list[2]) < 20:
                        region_dict[i][key] = str(
                            f'{birthdate_in_list[0]}.{birthdate_in_list[1]}.20{birthdate_in_list[2]}')
                    else:
                        region_dict[i][key] = str(
                            f'{birthdate_in_list[0]}.{birthdate_in_list[1]}.19{birthdate_in_list[2]}')
                else:
                    main_menu.textBrowser.append('\nНеврный формат даты!')

    one_result = {
        'id': None,
        'date': None,
        'region': None,
        'name': None,
        'exe_production': None,
        'details': None,
        'subject': None,
        'department': None,
        'bailiff': None,
        'ip_end': None
    }

    token_id = 0  # Будем перебирать ключи в процессе

    max_len_query_list = 50  # Максимальное число подзапросов в групповом запросе
    max_single_requests_per_hour = 100  # Максимальное число одиночных запросов в час
    max_single_requests_per_day = 1000  # Максимальное число одиночных запросов в сутки

    request_counter = 0  # счётчик запросов

    request = []  # формирую первый пакет на "запрос" мы будем записывать сюда номер человека и регион,
    # по которым сможем в дальнейшем определить, куда записывать полученные данные

    group_request_params = {"token": tokens[token_id], "request": []}  # сформируем параметры группового запроса

    for person in region_dict:
        for region in regions:
            if person[region] != 'X':
                request.append(
                    {"type": 1,
                     "params":
                         {"firstname": person["firstname"],
                          "lastname": person["lastname"],
                          "secondname": person["secondname"],
                          "region": region,
                          "birthdate": person["birthdate"]}
                     }
                )

            # если мы уже набрали 50 подзапросов или мы в конце списка, можно производить запрос
            if len(request) == max_len_query_list or (person == region_dict[-1] and region == regions[-1]):
                request_counter += 1
                group_request = requests.post(f'{URL}search/group', json=group_request_params).json()
                sleep(0.34)

                print('\nЗапрос', group_request)
                # '044c53e1-8aa5-4f2f-9fa4-f9028d5b00a7' id задачи
                group_request_task_id = group_request["response"]["task"]
                group_request_params["request"] = []


                request = []
    return None

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


def main():
    global main_menu
    app = QtWidgets.QApplication(sys_argv)  # Create application - инициализация приложения
    MainWindow = QtWidgets.QMainWindow()  # Create form main menu создание формы окна главного меню

    main_menu = Ui_MainWindow()
    main_menu.setupUi(MainWindow)
    MainWindow.show()

    main_menu.pushButton_search.clicked.connect(search)
    main_menu.pushButton_update.clicked.connect(update)

    main_menu.textBrowser.append("Программа 'Tywin' иницирована и готова к использованию\n"
                                 'Версия - Alpha 0.1\n'
                                 'Связь с автором - Григорий Скворцов GregoryValeryS@gmail.com\n'
                                 'GNU General Public License v3.0\n')

    sys_exit(app.exec_())  # Run main loop


if __name__ == '__main__':
    main()
