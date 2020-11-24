from requests import get, post
from math import ceil
from time import sleep
from pandas import DataFrame, read_excel
from sys import argv as sys_argv, exit as sys_exit
from PyQt5 import QtWidgets

from ui_window_main import Ui_MainWindow

global URL, TOKENS
URL = 'https://api-ip.fssprus.ru/api/v1.0/'  # на случай если сервер API изменится
# здесь вы указываете свой токен доступа C:/Google Drive/program/matirials_for_fssp_api/
TOKENS = open('C:/Google Drive/program/matirials_for_fssp_api/fssp_token.txt').read().split('\n')


def status(task: str):
    request = get(f'{URL}status', params={"token": TOKEN, "task": task}).json()


def search():
    push_request('search', TOKENS)


def update():
    push_request('update', TOKENS)


def push_request(search_or_update: str, tokens: list):
    # запишем данные из экселя и преобразуем их в список словарей
    region_excel_filename = main_menu.lineEdit_region_filename.text()
    result_excel_filename = main_menu.lineEdit_results_filename.text()
    # файл, с которым будете работать в формате колонок, X - не искать:
    # Фамилия   |   Имя   |   Отчество   | Дата рождения | 1 | 2 | 3 | 63 | ... и далее регионы
    # Навальный | Алексей | Анатольевич  | 04.06.1976    |   | X | X |    | ... .xlsx
    try:
        region_dict = read_excel(f'{region_excel_filename}.xlsx').to_dict(orient='records')
    except:
        main_menu.textBrowser.append('\nУкажите файл со списком людей и регионов.')
        return None

    # сгенерируем метаданные, ключи и все id
    region_keys_list = list(region_dict[0].keys())
    region_id_list = range(len(region_dict))
    regions = []

    # преобразуем формат даты в текст, удалим лишние пробелы, заменим 'nan' на пустые строки
    for key in region_keys_list:
        for i in region_id_list:
            region_dict[i][key] = str(region_dict[i][key]).replace(' ', '')

            if key == 'lastname' or key == 'firstname' or key == 'secondname':
                region_dict[i][key] = region_dict[i][key].title()

            if type(key) is int:
                regions.append(key)
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

    token_id = 0  # Будем перебирать ключи в процессе

    max_len_query_list = 50  # Максимальное число подзапросов в групповом запросе
    max_single_requests_per_hour = 100  # Максимальное число одиночных запросов в час
    max_single_requests_per_day = 1000  # Максимальное число одиночных запросов в сутки

    request_counter = 0  # счётчик запросов

    request = []  # формирую первый пакет на "запрос" мы будем записывать сюда номер человека и регион,
    # по которым сможем в дальнейшем определить, куда записывать полученные данные

    time_for_answer = ceil(3600 / ((max_single_requests_per_hour - 1) * len(tokens)))

    for p_id in range(len(region_dict)):
        for region in regions:
            if region_dict[p_id][region] != 'X':
                region_dict[p_id][region] = 'X'
                request.append(
                    {"type": 1,
                     "params":
                         {"firstname": region_dict[p_id]["firstname"],
                          "lastname": region_dict[p_id]["lastname"],
                          "secondname": region_dict[p_id]["secondname"],
                          "region": region,
                          "birthdate": region_dict[p_id]["birthdate"]}
                     }
                )

            # если мы уже набрали 50 подзапросов или мы в конце списка, можно производить запрос
            if (len(request) == max_len_query_list or (p_id == (len(region_dict) - 1) and region == regions[-1])) \
                    and len(request) != 0:

                if request_counter >= max_single_requests_per_hour:  # контролируем счетчик ключей
                    request_counter = 0
                    if token_id == (len(tokens) - 1):
                        token_id = 0
                    else:
                        token_id += 1
                request_counter += 1

                # сформируем параметры группового запроса
                group_request_params = {"token": tokens[token_id], "request": request}
                group_request = post(f'{URL}search/group', json=group_request_params).json()

                # 'a9dc76e4-9f00-41a0-b27b-78e5d7724b8d' id задачи group_request["response"]["task"]
                task_id = group_request["response"]["task"]
                print('\n', task_id, '\n')
                print(f'Дадим время на обратку запроса - {time_for_answer} сек.')
                sleep(time_for_answer)  # даем время на обработку запроса

                while True:

                    if request_counter >= max_single_requests_per_hour:  # контролируем счетчик ключей
                        request_counter = 0
                        if token_id == (len(tokens) - 1):
                            token_id = 0
                        else:
                            token_id += 1
                    request_counter += 1

                    params = {"token": tokens[token_id], "task": task_id}
                    answers = get(f'{URL}result', params=params).json()

                    if answers["response"]["task_end"] is not None:
                        print('Задача выполнена')
                        break
                    print(f'Сервера не отвечают, подождём ещё {time_for_answer} сек.')
                    sleep(time_for_answer)

                # Дозаписываем файл с результатами, считаем словарь
                try:
                    result_dict = read_excel(f'{result_excel_filename}.xlsx').to_dict(orient='records')
                except:
                    main_menu.textBrowser.append(f'\nФайл {result_excel_filename} не найден, или имеет неподходящий '
                                                 f'формат, или неверно структурирован\n')

                answer_counter = 0  # индекс результата совпадает с номером человека в запросе
                # для записи и обработки информации необходимо четко идентифицировать эти отношения

                # начинаем перечислять результаты запросов (по результату на человека (на подзапрос))
                answer_date = answers["response"]['task_end'][:10].replace('-', '.')
                for answer in answers["response"]["result"]:
                    if answer['result']:
                        for result in answer["result"]:
                            result_dict.append(
                                {'date': answer_date,
                                 'region': answer['query']['params']['region'],
                                 'lastname': answer['query']['params']['lastname'],
                                 'firstname': answer['query']['params']['firstname'],
                                 'secondname': answer['query']['params']['secondname'],
                                 'birthdate': answer['query']['params']['birthdate'],
                                 'name': result["name"],
                                 'exe_production': result["exe_production"],
                                 'details': result["details"],
                                 'subject': result["subject"],
                                 'department': result["department"],
                                 'bailiff': result["bailiff"],
                                 'ip_end': result["ip_end"]}
                            )

                    answer_counter += 1

                for result in result_dict:
                    print('\nЗаписано', result)

                request = []

                # преобразовываем обратно в data frame и перезаписываем файл в excel
                DataFrame.from_dict(region_dict).to_excel(f'{region_excel_filename}.xlsx', index=False)
                DataFrame.from_dict(result_dict).to_excel(f'{result_excel_filename}.xlsx', index=False)
                sleep(time_for_answer)

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
