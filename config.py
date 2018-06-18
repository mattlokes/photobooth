from functools import reduce
import operator

import yaml

class Config():
    def __init__( self, cfg_path):
        with open(cfg_path, 'r') as stream:
            try:
                self.raw_cfg = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def get( self, name):
        key_list = name.split("__")
        return self._get_flattened(key_list)

    def set( self, name, value):
        key_list = name.split("__")
        self._get_flattened( key_list[:-1])[key_list[-1]] = name

    def _get_flattened( self, kl):
        return reduce(operator.getitem, kl, self.raw_cfg)


