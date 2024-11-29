import user
import shopping_list

list_id = 0

# User Interaction
while True:
    print("\n\nOptions: ")
    print("1. New user")
    print("2. Existing user")
    choice = input("Enter your choice: ")

    if choice == "1":
        username = input("Enter your name: ")
        user_id = user.create_user(username)
        choice == "0"
        print("Options:")
        print("1. Create a new shopping list")
        print("2. Log out")
        choice = input("Enter your choice: ")
        if choice == "1":
            list_name = input("Enter the name for the new shopping list: ")
            list_id = shopping_list.create_shopping_list(list_name, user_id,)
            print(f"Created new shopping list with ID: {list_id}")
        elif choice == "2":
            continue
    elif choice == "2":
        username = input("\n\nUsername: ")
        while(not user.check_user_existence(username)):
            print("User does not exist!")
            username = input("\n\nUsername: ")
        choice == "0"
        print("Options:")
        print("1. Create a new shopping list")
        print("2. Enter an existing shopping list")
        choice = input("Enter your choice: ")
        if choice == "1":
            list_name = input("Enter the name for the new shopping list: ")
            list_id = shopping_list.create_shopping_list(list_name, user_id,)
            print(f"Created new shopping list with ID: {list_id}")
        elif choice == "2":
            list_id = str(input("Enter the ID of the existing shopping list: "))
            if shopping_list.check_list_existence(list_id):
                items = shopping_list.get_list_items(list_id)
                shopping_list.print_list_items(items)
            while(not shopping_list.check_list_existence(list_id)):
                print("List does not exist!")
                list_id = str(input("Enter the ID of the existing shopping list: "))
                items = shopping_list.get_list_items(list_id)
                shopping_list.print_list_items(items)
            
    
    while True:
        print("\nOptions for the shopping list:")
        print("1. Add item")
        print("2. Remove item")
        print("3. Back")
        # print("4. Refresh")
        list_choice = input("Enter your choice: ")

        if list_choice == "1":
            item_name = input("Enter the name of the item to add: ")
            item_quantity = input("Enter the quantity to add: ")
            shopping_list.add_item_to_list(list_id, item_name, item_quantity)

            items = shopping_list.get_list_items(list_id)
            shopping_list.print_list_items(items)
        elif list_choice == "2":
            items = shopping_list.get_list_items(list_id)
            shopping_list.print_list_items(items)
            if items:
                item_name = input("Enter the name of the item to remove: ")
                item_quantity = input("Enter the quantity to remove: ")
                shopping_list.remove_item_from_list(list_id, item_name, int(item_quantity))

                items = shopping_list.get_list_items(list_id)
                shopping_list.print_list_items(items)
            else:
                print("The list is empty.")
        elif list_choice == "3":
            break
            """ elif list_choice == "4":
                print_list_items(items)
                continue """
        else:
            print("Invalid choice")
    else:
        print("Invalid choice")