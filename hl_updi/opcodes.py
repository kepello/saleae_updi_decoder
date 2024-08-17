
OPCODES  = [
    # UNKNOWN
    {
        "name"      : 'LDS_0x02',
        "value"     : 0b00000010,
        "type"      : "unknown"
    },
    {
        "name"      : 'LDS_0x03',
        "value"     : 0b00000011,
        "type"      : "unknown",
        "ack"       : True
    },
    # POINTERS (Set)
    {
        "name"      : "LD ptr",
        "mask"      : 0b11101100,
        "value"     : 0b00101000,
        "address"   : "B",
        "type"      : "ptr"
    },
    {
        "name"      : "ST ptr",
        "mask"      : 0b11101100,
        "value"     : 0b01101000,
        "address"   : "B",
        "ack"       : True,
        "type"      : "ptr"
    },
    # LOAD (Get)
    {
        # Address, Data
        "name"      : "LDS",
        "mask"      : 0b11100000,
        "value"     : 0b00000000,
        "address"   : "A",
        "data"      : "B",
        "type"      : "get"
    },
    {
        # Register
        "name"      : "LDCS",
        "mask"      : 0b11100000,
        "value"     : 0b10000000,
        "data"      : "1",
        "register"  : "CS",
        "type"      : "get"
    },
    {
        # Data
        "name"      : "LD *(ptr)",
        "mask"      : 0b11101100,
        "value"     : 0b00100000,
        "data"      : "B",
        "type"      : "get"
    },
    {
        # Data
        "name"      : "LD *(ptr++)",
        "mask"      : 0b11101100,
        "value"     : 0b00100100,
        "data"      : "B",
        "type"      : "get"
    },
    {
        #Key
        "name"      : "KEY SIB",
        "mask"      : 0b11100100,
        "value"     : 0b11100100,
        "key"       : "B",
        "type"      : "get"
    },
    # SET (Write)
    {
        # Address, Data
        "name"      : "STS",
        "mask"      : 0b11100000,
        "value"     : 0b01000000,
        "address"   : "A",
        "data"      : "B",
        "ack"       : True,
        "type"      : "set"
    },
    {
        # Register
        "name"      : "STCS",
        "mask"      : 0b11100000,
        "value"     : 0b11000000,
        "data"      : "1",
        "register"  : "CS",
        "type"      : "set"
    },
    {
        # Data
        "name"      : "ST *(ptr)",
        "mask"      : 0b11101100,
        "value"     : 0b01100000,
        "data"      : "B",
        "ack"       : True,
        "type"      : "set"
    },
    {
        #Data
        "name"      : "ST *(ptr++)",
        "mask"      : 0b11101100,
        "value"     : 0b01100100,
        "data"      : "B",
        "ack"       : True,
        "type"      : "set"
    },
    {
        "name"      : "KEY",
        "mask"      : 0b11100100,
        "value"     : 0b11100000,
        "key"       : "B",
        "type"      : "set"
    },
    # REPEAT
    {
        "name"      : "REPEAT", 
        "mask"      : 0b11100000,
        "value"     : 0b10100000,
        "data"      : "B",
        "type"      : "repeat"
    }
]

ADDRESS_SIZE = {
    0x00 : 1,    # Byte
    0x01 : 2,    # Word
    0x02 : 3,    # 3 Bytes (For memories above 64K)
    0x03 : -1    # Reserved        
}

DATA_SIZE = {
    0x00 : 1,    # Byte
    0x01 : 2,    # Word
    0x02 : -1,   # Reserved
    0x03 : -1    # Reserved
}

KEY_SIZE = {
    0x00 : 8,    # 8 Bytes
    0x01 : 16,   # 16 Bytes
    0x02 : 32,   # 32 Bytes
    0x03 : 32    # Documented as Reserved, but observed to be used and returns 32 bytes
}
