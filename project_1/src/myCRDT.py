
import json

class DotContext:
    def __init__(self):
        self.cc = {}  

    def has(self, d):
        key, value = d
        if key in self.cc and value <= self.cc[key]:
            return True
        return False

    def next(self, id):
        if id in self.cc:
            self.cc[id] += 1
        else:
            self.cc[id] = 1
        return (id, self.cc[id])

    def join(self, other):
        for key, value in other.cc.items():
            if key in self.cc.keys():
                self.cc[key] = max(self.cc[key], value)
            else:
                self.cc[key] = value

    #def join(first, second):
    #    for key, value in second.cc.items():
    #        if key in first.cc.keys():
    #            first.cc[key] = max(first.cc[key], value)
    #        else:
    #            first.cc[key] = value
    #    return first

    def to_json(self):
        return json.dumps(self.cc)

    def print(self):
        print(self.to_json())
    
class CCounter:
    def __init__(self, node_id):
        self.node_id = node_id
        self.map = {}  #(id, count) -> value
        #if not context:
        #    self.context = context
        #else:
        self.context = DotContext()
    
    def inc(self, amount=1):
        base = 0
        delete_list = []
        for key, value in self.map.items():
            if (key[0] == self.node_id):
                base = max(base , value)
                delete_list.append(key)

        for key in delete_list:
            del self.map[key]
        
        dot = self.context.next(self.node_id)
        self.map[dot] = base + amount

    def dec(self, amount=1):
        #if (self.value() - amount < 0):
        #    amount = value - self.value() 
        base = 0
        delete_list = []
        for key, value in self.map.items():
            if (key[0] == self.node_id):
                base = max(base , value)
                delete_list.append(key)

        for key in delete_list:
            del self.map[key]

        dot = self.context.next(self.node_id)
        self.map[dot] = base - amount
    
    def value(self):
        result = 0
        for value in self.map.values():
            result += value
        return result
    

    def merge(self, other):
        it = iter(self.map.items())
        ito = iter(other.map.items())

        it_key, _ = next(it, (None, None))
        ito_key, ito_val = next(ito, (None, None))

        delete_list = []
        append_disc = {}

        while it_key is not None or ito_key is not None:
            if it_key is not None and (ito_key is None or it_key < ito_key):
                # Dot only at this
                if other.context.has(it_key):  # Other knows dot, must delete here
                    delete_list.append(it_key)  # Store the current key
                    it_key, _ = next(it, (None, None))  # Advance iterator
                else:  # Keep it
                    it_key, _ = next(it, (None, None))
            elif ito_key is not None and (it_key is None or ito_key < it_key):
                # Dot only at other
                if not self.context.has(ito_key):  # If I don't know, import
                    append_disc[ito_key] = ito_val
                ito_key, ito_val = next(ito, (None, None))
            elif it_key is not None and ito_key is not None:
                # Dot in both
                it_key, _ = next(it, (None, None))
                ito_key, ito_val = next(ito, (None, None))
        
        self.map = self.map | append_disc
        
        for key in delete_list:
            del self.map[key]
        
        self.context.join(other.context)

    def reset(self):
        self.map.clear()

    def to_json(self):
        result = {
            "map": self.map,
            "context": self.context.to_json()
        }
        return result
    
    def print(self):
        print(self.to_json())


class AWMap:
    def __init__(self, node_it):
        self.node_it = node_it
        self.map = {} # product -> CCounter
        self.itemContext = {} #product -> ContextItem
        self.context = DotContext()

    def add_item(self, item_name, amount):
        dot = self.context.next(self.node_it)
        if item_name not in self.map:
            self.map[item_name] = CCounter(self.node_it)
            self.itemContext.setdefault(item_name, {})[self.node_it] = dot[1]
        else:
            self.itemContext.setdefault(item_name, {})[self.node_it] = dot[1]
        if amount > 0:
            self.map[item_name].inc(amount)
        else:
            self.map[item_name].dec(-amount)
 
    def remove_item(self, item_name):
        if item_name in self.map:
            self.map[item_name].reset()
            self.itemContext[item_name].clear()

    #def update_item(self, item_name, amount):
    #    if(item_name not in self.map.keys()):
    #        self.add_item(item_name)
#
    #    if(not self.itemContext[item_name]): return
#
    #    dot = self.context.next(self.node_it)
    #    if amount > 0:
    #        self.map[item_name].inc(amount)
    #    else:
    #        self.map[item_name].dec(-amount)
    #    self.itemContext[item_name][dot[0]] = dot[1]

    def item_value(self, item_name):
        if item_name in self.map and not self.itemContext[item_name]:
            return  self.map[item_name].value()
        return 0

    def values(self):
        values = {}
        for item_name in self.map:
            if not self.itemContext[item_name]:
                values[item_name] = self.map[item_name].value()
        return values

    def merge(self, other):
        for item_name in other.map:
            if item_name in self.map:
                if(self.itemContext[item_name] == other.itemContext[item_name]):
                    self.map[item_name].merge(other.map[item_name])
                else:
                    self.map[item_name].merge(other.map[item_name])
                    merge_item_context = {}
                    
                    for id, count in self.itemContext[item_name].items():
                        if(not other.context.has((id,count))):
                            merge_item_context[id] = count

                    for id, count in other.itemContext[item_name].items():
                        if(not self.context.has((id,count))):
                            merge_item_context[id] = count

                    self.itemContext[item_name] = merge_item_context
            else:
                self.map[item_name] = other.map[item_name]
                self.itemContext[item_name] = other.itemContext[item_name]

        self.context.join(other.context)
    
    def print_dict(self):
        l = []
        for product in self.map.keys():
            ele = {
                "product": product,
                "value": self.map[product].value(),
                "value context": self.map[product].to_json(),
                "contxt Item": self.itemContext[product],
            }
            l.append(ele)
            print(ele)
        
        dict = {
            "context":self.context.to_json()
        }
        print(dict)
 
