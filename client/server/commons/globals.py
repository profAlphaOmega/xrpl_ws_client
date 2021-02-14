import time


class GlobalsBorg:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state


class Globals(GlobalsBorg):
    '''Data Structure meant to facilitate Global Variables
    '''

    def __init__(self):
        GlobalsBorg.__init__(self)
        if '_GLOBALS' not in self.__dict__:
            self._GLOBALS: Dict = {
                'zato_start_time': str(time.time()),
                'zato_end_time': '',
                'zato_errors': list(),
                'starting_ledger_index': '',
                'current_ledger_index': '',
                'xrp_to_drops': 1000000,
                'run_data': {
                    'default_id': {
                        'id': str(time.time()),
                        'shell': 'agent',
                        'type': 'agent',
                        'start_time': '',
                        'finish_time': '',
                        'errors': list(),
                        'rates': list(),
                        'trades': dict(),
                        'duplicate_trades': list(),
                        'opps': list(),
                        'ledger_index': '',
                    },
                }
            }
        
    @property
    def xrp_to_drops(self):
        return int(self._GLOBALS['xrp_to_drops'])
    
    @property
    def current_ledger_index(self):
        return str(self._GLOBALS['current_ledger_index'])

    @current_ledger_index.setter
    def current_ledger_index(self, value):
        self._GLOBALS['current_ledger_index'] = str(value)
    
    @property
    def starting_ledger_index(self):
        return str(self._GLOBALS['starting_ledger_index'])

    @starting_ledger_index.setter
    def starting_ledger_index(self, value):
        self._GLOBALS['starting_ledger_index'] = str(value)
    
