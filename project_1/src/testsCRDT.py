from myCRDT import CCounter, AWMap


if __name__ == "__main__":

    m1 = AWMap("A")
    m2 = AWMap("B")

    m1.add_item("bananas", 4)
    m1.add_item("apples",2)

    m2.add_item("bananas",2)
    m2.add_item("oranges", 3)

    m1.merge(m2)

    print('\n')
    m2.print_dict()

    m2.merge(m1)

    print("Join FIRST")
    m1.print_dict()
    print('\n')
    m2.print_dict()

    print('\n')
    print('DELETE bananas A')
    m1.remove_item("bananas")
    m1.print_dict()
    print('\n')

    print('Aumnetar bananas B')
    m2.add_item("bananas",2)
    m2.print_dict()
    
    print('\n')

    m2.merge(m1)
    m1.merge(m2)

    print("Join Second")
    m1.print_dict()
    print('\n')
    m2.print_dict()

    print('\n')

    print("merge 3")
    m2.merge(m1)
    m1.merge(m2)

    m1.print_dict()
    print('\n')
    m2.print_dict()


    m1.remove_item("orange")

    m2.add_item("oranges", 3)

    m3 = AWMap("C")

    m3.merge(m1)
    m3.merge(m2)

    print("\n")
    m3.print_dict()

    print('\n')
    

    m1.add_item("bananas",2)
    m1.print_dict()
    print('\n')


    m1.merge(m2)
    m1.print_dict()
    print('\n')




