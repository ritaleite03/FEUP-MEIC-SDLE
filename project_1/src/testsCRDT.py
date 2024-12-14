from myCRDT import CCounter, AWMap


if __name__ == "__main__":

    m1 = AWMap("A")
    m2 = AWMap("B")

    m1.add_item("bananas", 4)
    m1.add_item("apples",2)

    m2.add_item("bananas",2)
    m2.add_item("oranges", 3)

    m1.merge(m2)
    m2.merge(m1)

    print("Join FIRST")
    print(m1.values())
    print(m1.itemContext)
    print('\n')

    print('DELETE bananas A')
    m1.remove_item("bananas")
    print(m1.values())
    print(m1.itemContext)
    print('\n')

    print('Aumnetar bananas B')
    #m2.update_item("bananas", 2)
    m2.add_item("bananas",2)
    print(m2.values())
    print(m2.itemContext)
    
    print('\n')

    m2.merge(m1)
    m1.merge(m1)

    print(m2.values())
    print('\n')

    m2.merge(m1)
    m1.merge(m1)

    print(m2.values())
    print('\n')
    
    print(m1.values())
    print(m2.values())

#    print("TESTE")
#    m1.add_item("bananas",2)
#    m1.print_dict()
#    print('\n')
#
#
#    m1.merge(m2)
#    m1.print_dict()
#    print('\n')





