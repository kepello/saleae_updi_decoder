from enum import IntEnum, Enum

OPCODES  = [
    {
        "name"      : 'BREAK',
        "mask"      : 0b11111111,
        "value"     : 0x00
    },
    {
        "name"      : "LDS",
        "mask"      : 0b11100000,
        "value"     : 0b00000000,
        "address"   : "A",
        "data"      : "B",
        "operator"  : "==" 
    },
    {
        "name"      : "STS",
        "mask"      : 0b11100000,
        "value"     : 0b01000000,
        "address"   : "A",
        "data"      : "B",
        "operator"  : "=",
        "ack"       : True
    },
    {
        "name"      : "LDCS",
        "mask"      : 0b11100000,
        "value"     : 0b10000000,
        "data"      : "1",
        "register"  : "CS",
        "operator"  : "==" 
    },
    {
        "name"      : "STCS",
        "mask"      : 0b11100000,
        "value"     : 0b11000000,
        "data"      : "1",
        "register"  : "CS",
        "operator"  : "=" 
    },
    {
        "name"      : "ST *(ptr)",
        "mask"      : 0b11101100,
        "value"     : 0b01100000,
        "data"      : "B",
        "operator"  : "=",
        "ack"       : True
    },
    {
        "name"      : "ST *(ptr++)",
        "mask"      : 0b11101100,
        "value"     : 0b01100100,
        "data"      : "B",
        "operator"  : "=",
        "ack"       : True 
    },
    {
        "name"      : "ST ptr",
        "mask"      : 0b11101100,
        "value"     : 0b01101000,
        "address"   : "B",
        "operator"  : "=",
        "ack"       : True 
    },
    {
        "name"      : "LD *(ptr)",
        "mask"      : 0b11101100,
        "value"     : 0b00100000,
        "data"      : "B",
        "operator"  : "=" 
    },
    {
        "name"      : "LD *(ptr++)",
        "mask"      : 0b11101100,
        "value"     : 0b00100100,
        "data"      : "B",
        "operator"  : "=" 
    },
    {
        "name"      : "LD ptr",
        "mask"      : 0b11101100,
        "value"     : 0b00101000,
        "address"   : "B",
        "operator"  : "=" 
    },
    {
        "name"      : "REPEAT", 
        "mask"      : 0b11100000,
        "value"     : 0b10100000,
        "data"      : "B",
        "operator"  : "*"
    },
    {
        "name"      : "KEY SIB",
        "mask"      : 0b11100100,
        "value"     : 0b11100100,
        "key"       : "B",
        "operator"  : "="
    },
    {
        "name"      : "KEY SIB",
        "mask"      : 0b11100100,
        "value"     : 0b11100000,
        "operator"  : "==",
        "key"       : "B"
    }

]
