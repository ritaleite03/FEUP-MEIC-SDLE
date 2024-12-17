import ast
import json
import time

from numpy import sort

class DotContext:
    def __init__(self, cc=None):
        self.cc = cc if cc is not None else {}

    def has(self, d):
        key, value = d
        return key in self.cc and value <= self.cc[key]

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

    def to_dict(self):
        return {k: v for k, v in self.cc.items()}

    @classmethod
    def from_dict(cls, cc):
        return cls(cc)


class CCounter:
    def __init__(self, map=None, context=None):
        self.map = map if map is not None else {}  # (id, count) -> value
        self.context = DotContext.from_dict(context if context is not None else {})

    def inc(self, node_id, amount=1):
        base = 0
        delete_list = []
        for key, value in self.map.items():
            if key[0] == node_id:
                base = max(base, value)
                delete_list.append(key)
        for key in delete_list:
            del self.map[key]
        dot = self.context.next(node_id)
        self.map[dot] = base + amount

    def dec(self, node_id, amount=1):
        base = 0
        delete_list = []
        for key, value in self.map.items():
            if key[0] == node_id:
                base = max(base, value)
                delete_list.append(key)
        for key in delete_list:
            del self.map[key]
        dot = self.context.next(node_id)
        self.map[dot] = base - amount

    def value(self):
        return sum(self.map.values())

    def merge(self, other):
               
        self.map = {k: self.map[k] for k in sorted(self.map)}
        other.map = {k: other.map[k] for k in sorted(other.map)}
        
        it = iter(self.map.items())
        ito = iter(other.map.items())
        it_key, _ = next(it, (None, None))
        ito_key, ito_val = next(ito, (None, None))
        delete_list = []
        append_disc = {}
        
        while it_key is not None or ito_key is not None:
            
            if it_key is not None and (ito_key is None or it_key < ito_key):
                if other.context.has(it_key):  # Other knows dot, must delete here
                    delete_list.append(it_key)
                    it_key, _ = next(it, (None, None))
                else:
                    it_key, _ = next(it, (None, None))
        
            elif ito_key is not None and (it_key is None or ito_key < it_key):
                
                if not self.context.has(ito_key):  # If I don't know, import
                    append_disc[ito_key] = ito_val
                ito_key, ito_val = next(ito, (None, None))
        
            elif it_key is not None and ito_key is not None:
                #self.map[it_key] = max(self.map[it_key], ito_val)
                it_key, _ = next(it, (None, None))
                ito_key, ito_val = next(ito, (None, None))
        
        self.map = self.map | append_disc

        for key in delete_list:
            del self.map[key]

        self.context.join(other.context)

    def reset(self):
        self.map.clear()

    def to_dict(self):
        return {
            "map": {k: v for k, v in self.map.items()},  # Serialize keys as strings
            "context": self.context.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        map_converted = {k: v for k, v in data["map"].items()}  # Deserialize keys
        return cls(map_converted, data["context"])


class AWMap:
    def __init__(self, node_it, map=None, itemContext=None, context=None):
        self.node_it = node_it
        self.map = map if map is not None else {}  # product -> CCounter
        self.itemContext = itemContext if itemContext is not None else {}  # product -> ContextItem
        self.context = DotContext.from_dict(context if context is not None else {})

    def add_item(self, item_name, amount):
        dot = self.context.next(self.node_it)
        if item_name not in self.map:
            self.map[item_name] = CCounter()
            self.itemContext.setdefault(item_name, {})[self.node_it] = dot[1]
        else:
            self.itemContext.setdefault(item_name, {})[self.node_it] = dot[1]
        if amount > 0:
            self.map[item_name].inc(self.node_it, amount)
        else:
            self.map[item_name].dec(self.node_it, -amount)

    def remove_item(self, item_name):
        if item_name in self.map:
            self.map[item_name].reset()
            self.itemContext[item_name].clear()

    def item_value(self, item_name):
        if item_name in self.map and len(self.itemContext[item_name]) != 0:
            return self.map[item_name].value()
        return 0

    def values(self):
        values = {}
        for item_name in self.map:
            if len(self.itemContext[item_name]) != 0:
                values[item_name] = self.map[item_name].value()
        
        return values

    def merge(self, other):
        for item_name in other.map:
            if item_name in self.map:
                if self.itemContext[item_name] == other.itemContext[item_name]:
                    self.map[item_name].merge(other.map[item_name])
                else:                   
                    self.map[item_name].merge(other.map[item_name])
                    merge_item_context = {}

                    for key, value in self.itemContext[item_name].items():
                        if key in other.itemContext[item_name].keys() and other.itemContext[item_name][key] == value:
                            merge_item_context[key] = value

                    for id, count in self.itemContext[item_name].items():
                        if not other.context.has((id, count)):
                            merge_item_context[id] = count
                            
                    for id, count in other.itemContext[item_name].items():
                        if not self.context.has((id, count)):
                            merge_item_context[id] = count
                    self.itemContext[item_name] = merge_item_context
            else:
                self.map[item_name] = other.map[item_name]
                self.itemContext[item_name] = other.itemContext[item_name]

        self.context.join(other.context)

    def to_dict(self):
        return {
            "node_it": self.node_it,
            "map": {k: v.to_dict() for k, v in self.map.items()},
            "itemContext": self.itemContext,
            "context": self.context.to_dict(),
        }
    
    def print_dict(self):
        dict = self.to_dict()
        print(dict["node_it"])
        for key, value in dict["map"].items():
            print(key, "->", value)
        print(dict["itemContext"])
        print(dict["context"])

    @classmethod
    def from_dict(cls, node_id, data):
        data = ast.literal_eval(data)
        map_converted = {k: CCounter.from_dict(v) for k, v in data["map"].items()}
        return cls(node_id, map_converted, data["itemContext"], data["context"])
