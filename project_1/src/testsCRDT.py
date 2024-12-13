from myCRDT import CCounter, AWMap


if __name__ == "__main__":
    #x = CCounter("a")
    #y = CCounter("b")
#
    #x.inc(4)
    #x.print()
    #x.dec()
    #x.print()
    #y.dec()
    #y.print()
    #print(x.value())
    #print(y.value())
    #print(x.value() == y.value())
    #x.merge(y)
    #y.merge(x)
    #print("join A ")
    #x.print()
    #print("join B")
    #y.print()
    #print(x.value() == y.value())
    #x.reset()
    #print(x.value())
    #x.print()
    #x.merge(y)
    #y.merge(x)
    #print("Join")
    #x.print()
    #y.print()
    #x.inc(4)
    #y.dec()
    #print("add")
    #print(x.value())
    #print(y.value())
    #x.print()
    #y.print()

    m1 = AWMap("A")
    m2 = AWMap("B")

    m1.add_item("bananas", 4)
    #m1.update_item("bananas", 4)
    m1.add_item("apples",2)
    #m1.update_item("apples", 2)

    m2.add_item("bananas",2)
    #m2.update_item("bananas",2)
    m2.add_item("oranges", 3)
    #m2.update_item("oranges",3)

    #m1.print_dict()
    print('\n')

    #m2.print_dict()
    print('\n')

    m1.merge(m2)
    m2.merge(m1)

    print("Join FIRST")
    m1.print_dict()
    print('\n')

    print('DELETE bananas A')
    m1.remove_item("bananas")
    m1.print_dict()
    print('\n')

    print('Aumnetar bananas B')
    #m2.update_item("bananas", 2)
    m2.add_item("bananas",2)
    m2.print_dict()
    print('\n')

    m2.merge(m1)
    m1.merge(m1)

    m2.print_dict()
    print('\n')

    m2.merge(m1)
    m1.merge(m1)

    m2.print_dict()
    print('\n')

#    print("TESTE")
#    m1.add_item("bananas",2)
#    m1.print_dict()
#    print('\n')
#
#
#    m1.merge(m2)
#    m1.print_dict()
#    print('\n')





