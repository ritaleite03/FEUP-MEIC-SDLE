import os


def option_menu(menu_text, min, max):
    option = 0
    while True:
        option = menu(menu_text)
        try:
            option = int(option)
            if min < option < max: break
            else: print_error("The option does not exist")
        except ValueError:
            print_error("The option is not a number") 
    return option


def name_menu(menu_text):
    option = menu(menu_text)
    return option


def quantity_item_menu(menu_text):
    option_number = 0
    option_string = ''
    while True:
        option = menu(menu_text).split(' ')
        try:
            option_number = int(option[0])
            option_string = option[1]
            return option_number, option_string   
        except ValueError:
            print_error("The option is not a number") 


def menu(menu):
    os.system('clear')
    for line in menu:
        print(line)
    return input("\nWrite here : ").lower()


def print_error(message):
    input("\nAn error has occured !\n" + message + "\nPress any key.")