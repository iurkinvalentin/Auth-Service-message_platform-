import sys
import os


def replace_double_quotes_in_file(file_path):
    # Читаем содержимое файла
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Заменяем двойные кавычки на одинарные
    content = content.replace('"', "'")

    # Перезаписываем файл с изменённым содержимым
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def main():
    # Проверяем, передано ли имя файла
    if len(sys.argv) != 2:
        print("Usage: python replace_quotes.py <filename>")
        sys.exit(1)

    # Получаем имя файла из аргумента командной строки
    file_path = sys.argv[1]

    # Проверяем, существует ли файл и имеет ли он расширение .py
    if os.path.isfile(file_path) and file_path.endswith(".py"):
        replace_double_quotes_in_file(file_path)
        print(f"Processed file: {file_path}")
    else:
        print("Error: File not found or not a .py file")


# Запуск основной функции
if __name__ == "__main__":
    main()
