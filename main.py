import requests
import json
from time import sleep

global URL, ACCESS_TOKEN
URL = 'https://api.vk.com/method/'
ACCESS_TOKEN = open('C:/Google Drive/other/token.txt').read()  # здесь вы указываете путь к своему токену доступа

def write_json_in_file(data):
    """функция получет json-данные и записывает их в файл data.json"""
    with open('data.json', 'w') as file:  # создаём/открываем файл data
        # и сохраняем данные файла в переменную file
        json.dump(data, file, indent=2, ensure_ascii=False)

def main():
    request_type = 'people'

    params = {
        'access_token': ACCESS_TOKEN
    }

    offset = 0
    params.update({'offset': offset})

    sleep(0.34)
    request = requests.get(f'{URL}{request_type}?', params=params).json()
    print(request)

if __name__ == '__main__':
    main()
