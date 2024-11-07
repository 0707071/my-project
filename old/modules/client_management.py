# modules/client_management.py

import os
import json
from datetime import datetime

def create_project_structure(config):
    client_name = config['client_name']
    search_date = datetime.now()

    # Корневая папка проекта
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)  # Поднимаемся на уровень выше

    # Папка результатов
    results_dir = os.path.join(project_root, 'results')
    os.makedirs(results_dir, exist_ok=True)

    # Папка клиента
    client_dir = os.path.join(results_dir, client_name)
    os.makedirs(client_dir, exist_ok=True)

    # Папка ролей
    roles_dir = os.path.join(client_dir, 'roles')
    os.makedirs(roles_dir, exist_ok=True)

    # Файлы в папке ролей
    prompt_file = os.path.join(roles_dir, 'prompt.txt')
    search_query_file = os.path.join(roles_dir, 'search_query.json')

    with open(prompt_file, 'w') as f:
        f.write(config['prompt'])

    with open(search_query_file, 'w') as f:
        json.dump(config['search_queries'], f)

    # Папка текущего поиска
    search_date_str = search_date.strftime('%Y-%m-%d')
    current_search_dir = os.path.join(client_dir, search_date_str)
    os.makedirs(current_search_dir, exist_ok=True)

    # Создание пустых файлов для текущего поиска
    files_in_search = [
        'search_results.csv',
        'search_results_cleaned.csv',
        'search_results_analysed.csv'
    ]
    for file in files_in_search:
        open(os.path.join(current_search_dir, file), 'w').close()

    print(f"Структура папок и файлов создана для клиента '{client_name}' и даты '{search_date_str}'.")

def select_client():
    clients_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
    clients = [d for d in os.listdir(clients_dir) if os.path.isdir(os.path.join(clients_dir, d))]

    print("Доступные клиенты:")
    for i, client in enumerate(clients):
        print(f"{i + 1}. {client}")

    client_index = int(input("Выберите клиента (введите номер): ")) - 1
    return clients[client_index]

def get_client_and_date():
    clients_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
    clients = [d for d in os.listdir(clients_dir) if os.path.isdir(os.path.join(clients_dir, d))]

    print("Доступные клиенты:")
    for i, client in enumerate(clients, 1):
        print(f"{i}. {client}")
    print("0. Создать нового клиента")
    
    while True:
        choice = input("Выберите клиента (введите номер): ")
        if choice == '0':
            with open('config/new_client_profile.json', 'r') as f:
                config = json.load(f)
            create_project_structure(config)
            client_name = config['client_name']
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(clients):
            client_name = clients[int(choice) - 1]
            break
        else:
            print("Неверный выбор. Попробуйте еще раз.")

    date_input = input("Введите дату поиска (в формате YYYY-MM-DD) или нажмите Enter для текущей даты: ")
    if date_input.strip() == "":
        search_date = datetime.now()
    else:
        search_date = datetime.strptime(date_input, '%Y-%m-%d')

    return client_name, search_date

    return client_name, search_date