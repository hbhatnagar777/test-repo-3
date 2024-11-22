import configparser
import threading

def enum(**enums):
    return type('Enum',(), enums)

class AC_ConfigParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d
    
def threadLauncher(tCount, q, target):        
    for i in range(tCount):
        theThread           =   threading.Thread(target=target, args=(i, q))
        theThread.daemon    =   True
        theThread.start()
    
    return True