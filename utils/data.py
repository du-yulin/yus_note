"""处理数据相关工具"""
from typing import Union


def trim(data:Union[dict,list], key, value):
    """递归删除data下有key:value的数据"""
    if isinstance(data,dict):
        for k,v in data.items():
            if k==k and v==value:
                return None
            elif isinstance(v, (dict, list)):
                data[k] = trim(v, key, value) 
    if isinstance(data,list):
        for i in range(len(data)):
            data[i] = trim(data[i],key,value)
            if data[i]==None:
                del data[i]
        return data
    return data

        





