import os


def get_lists_to_string(lists):
    lists_string = "You hava already this lists saved:"
    if(len(lists) == 0):
        return "There is no list saved.\n"
    for (name, url, owner) in lists:
        lists_string += "URL : " + url + " , " + "Name : " + name + " , " + "Owner : " + str(owner) + "\n"
    return lists_string


def get_list_items_to_string(items):
    items_string = "Here is the content of this list:"
    if(len(items) == 0):
        return "This list is empty.\n"
    for (name, quantity) in items:
        items_string += "Item : " + name + " , " + "Quantity : " + str(quantity) + "\n"
    return str(items_string)   
    
    
def option_menu(menu_text, min, max, last_line = None):
    option = 0
    while True:
        option = menu(menu_text, last_line)
        try:
            option = int(option)
            if min < option < max: break
            else: print_error("The option does not exist")
        except ValueError:
            print_error("The option is not a number") 
    return option


def name_menu(menu_text, last_line = None):
    option = menu(menu_text, last_line)
    return option


def quantity_item_menu(menu_text, last_line = None):
    option_number = 0
    option_string = ''
    while True:
        option = menu(menu_text, last_line).split(' ')
        try:
            option_number = int(option[0])
            option_string = option[1]
            return option_number, option_string   
        except ValueError:
            print_error("The option is not a number") 


def menu(menu, last_line = None):
    os.system('clear')
    for line in menu:
        print(line)
    if(last_line != None):
        print("\n" + last_line)
    return input("\nWrite here : ").lower()


def print_error(message):
    input("\nAn error has occured !\n" + message + "\nPress any key.")