from typing import Dict

class PNCounter:
    
    def __init__(self, positive=0, negative=0):
        self.positive = positive
        self.negative = negative
    
    def increment(self, quantity): 
        self.positive += quantity
    
    def decrement(self, quantity): 
        self.negative += quantity
        
    def compare(self, other):
        return self.positive == other.positive and self.negative == other.negative
        
    def value(self): 
        return self.positive - self.negative
    
    def merge(self, other):
        self.positive = max(self.positive, other.positive)
        self.negative = max(self.negative, other.negative)
    
    def to_dict(self):
        return {"positive": self.positive, "negative": self.negative}

 
class ShoppingList:
    
    def __init__(self):
        self.items : Dict[str, PNCounter] = {}
    
    def add_item(self, name, quantity):
        if name not in self.items.keys(): self.items[name] = PNCounter(quantity, 0)
        else: self.items[name].increment(quantity)
    
    def del_item(self, name, quantity):
        self.items[name].decrement(quantity)
        if (self.items[name].value() <= 0): del self.items[name]
    
    def to_dict(self):
        return { key: value.to_dict() for key, value in self.items.items() }

    def from_dict(self, data: Dict) -> 'ShoppingList':
        shopping_list = ShoppingList()
        for key, value in data.items():
            shopping_list.items[key] = PNCounter(**value)      
        return shopping_list
        
    def merge(self, other):
        
        merge_dict = {}
        # add new items from self and other
        for key, counter in self.items.items():
            if key not in other.items: merge_dict[key] = counter 
        for key, counter in other.items.items():
            if key not in self.items: merge_dict[key] = counter      
        # deal with conflicts
        for key, counter in other.items.items():     
            if key not in self.items: continue
            equal = self.items[key].compare(other.items[key])
            if equal:
                merge_dict[key] = self.items[key]
            else:
                self.items[key].merge(other.items[key])
                merge_dict[key] = self.items[key]        
        # update 
        self.items = merge_dict
        
