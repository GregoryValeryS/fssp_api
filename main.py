import requests
import json
from time import sleep

global URL, ACCESS_TOKEN
URL = 'https://api-ip.fssprus.ru/api/v1.0/'
TOKEN = open('C:/Google Drive/other/fssp_token.txt').read()  # здесь вы указываете путь к своему токену доступа


def write_json_in_file(data):
    """функция получет json-данные и записывает их в файл data.json"""
    with open('data.json', 'w') as file:  # создаём/открываем файл data
        # и сохраняем данные файла в переменную file
        json.dump(data, file, indent=2, ensure_ascii=False)


def group_request():
    request_type = 'search/group'

    request_params = {"token": TOKEN,  # Ключ доступа к API Обязательный параметр
                      "request": []}

    person_params = {
        "firstname": "Григорий",
        "lastname": "Скворцов",
        "secondname": "Валерьевич",
        "region": 56,
        "birthdate": "17.07.1994"
    }

    request_params["request"].append(
        {
            "type": 1,  # Обязательный параметр, который обозначает тип запроса, может быть один из:
            # 1 - Отправить запрос на поиск физического лица;
            # 2 - Отправить запрос на поиск юридического лица;
            # 3 - Отправить запрос на поиск по номеру исполнительного производства;
            "params": person_params
        }
    )

    print(request_params)

    sleep(0.34)
    request = requests.get(f'{URL}{request_type}', params=request_params).json()
    print(request)


def person_request():
    request_type = 'search/physical'

    request_params = {
        "token": TOKEN,  # Ключ доступа к API Обязательный параметр
    }

    request_params.update(
        {
            "firstname": "Григорий",
            "lastname": "Скворцов",
            "secondname": "Валерьевич",
            "region": 56,
            "birthdate": "17.07.1994"
        }
    )

    print(request_params)

    sleep(0.34)
    request = requests.get(f'{URL}{request_type}', params=request_params).json()
    print(request)


def person_status():
    request_type = 'status'

    request_params = {
        "token": TOKEN,  # Ключ доступа к API Обязательный параметр
    }

    request_params.update(
        {
            "task": "a3527600-1118-47cb-ba41-3ffa40291092"
        }
    )

    print(request_params)

    sleep(0.34)
    request = requests.get(f'{URL}{request_type}', params=request_params).json()
    print(request)


def person_result():
    request_type = 'result'

    request_params = {
        "token": TOKEN,  # Ключ доступа к API Обязательный параметр
    }

    request_params.update(
        {
            "task": "a3527600-1118-47cb-ba41-3ffa40291092"
        }
    )

    print(request_params)

    sleep(0.34)
    request = requests.get(f'{URL}{request_type}', params=request_params).json()
    print(request)


if __name__ == '__main__':
    task = 'a3527600-1118-47cb-ba41-3ffa40291092'
    person_result()
