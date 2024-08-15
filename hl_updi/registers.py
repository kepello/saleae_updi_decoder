REGISTERS = [
    { 
        "number"    : 0x00,
        "name"      : 'STATUSA',
        "components"    :  [ 
            { 
                "mask"      : 0b11110000,
                "shift"     : 4,
                "name"      : "UPDIREC"
            },
            {
                "bits"       : [3,2,1,0]
            }
        ]
    },
    { 
        "number"    : 0x01,
        "name"      : 'STATUSB',
        "components"    :  [ 
            {
                "bits"      : [7,6,5,4,3]
            },
            { 
                "name"      : "PESIG",
                "mask"      : 0b00000111,
                "values"    : { 
                    0x00 : "No Error"  ,
                    0x01 : "Parity Error" ,
                    0x02 : "Frame Error" ,
                    0x03 : "Access Layer Timeout Layer" ,
                    0x04 : "Clock Recovery Error" ,
                    0x05 : "Reserved" ,
                    0x06 : "Bus Error" ,
                    0x07 : "Contention Error" 
                }
            } ,

        ]
    },
    { 
        "number"    : 0x02,
        "name"      : 'CTRLA',
        "components"    : [ 
            {
                "name"      : "IBDLY",
                "bit"       : 7,
                "values"    : { 
                    0 : "Disabled" , 
                    1 : "Enabled"  
                }
            },
            {
                "bit"       : 6
            },
            {
                "name"      : "PARD",
                "bit"       : 5,
                "values"    : {
                    0 : 'Enabled',
                    1 : 'Disabled'
                }
            },
            {
                "name"      : "DTD",
                "bit"       : 4,
                "values"    : {
                    0 : 'Enabled',
                    0 : 'Disabled'
                }
            },
            {
                "name"      : "RSD",
                "bit"       : 3,
                "values"    : {
                    0 : 'Enabled',
                    1 : 'Disabled'
                }
            },
            {
                "name"      : "GTVAL",
                "mask"      : 0x00000111,
                "values"    : {
                    0 : '128 Cycles',
                    1 : '64 Cycles',
                    2 : '32 Cycles',
                    3 : '16 Cycles',
                    4 : '8 Cycles',
                    5 : '4 Cycles',
                    6 : '2 Cycles',
                    7 : 'RESERVED'
                }
            }
        ]
    },    
    { 
        "number"    : 0x03,
        "name"      : 'CTRLB',
        "components"    : [ 
            {
                "bits"      : [7,6,5]
            },
            {
                "name"      : "NAKDIS",
                "bit"       : 4,
                "values"    : { 
                    0 : "Enabled" , 
                    1 : "Disabled"  
                }
            },
            {
                "name"      : "CCDETDIS",
                "bit"       : 3,
                "values"    : { 
                    0 : "Enabled" , 
                    1 : "Disabled"  
                }
            },
            {
                "name"      : "UPDIDIS",
                "bit"       : 2,
                "values"    : { 
                    0 : "Enabled" , 
                    1 : "Disabled"  
                }
            },
            {
                "bits"      : [1,0]
            }
        ]
    },    
    { 
        "number"    : 0x04,
        "name"      : 'ASI_OCD_CTRLA',
        "components"    : [
            {
                "bit"   : 7,
                "name"  : "SOR_DIR"
            },
            {
                "bits"  : [6,5,4,3,2]
            },
            {
                "bit"   : 1,
                "name"  : "RUN"
            },
            {
                "bit"   : 0,
                "name"  : "STOP"
            },
        ]
    },    
    { 
        "number"    : 0x05,
        "name"      : 'ASI_OCD_STATUS',
        "components"    : [
            {
                "bit"   : 4,
                "name"  : 'OCDMV'
            },
            {
                "bit"   : 0,
                "name"  : 'STOPPED'
            }
        ]
    },     
    { 
        "number"    : 0x06,
        "name"      : 'RESERVED_06X',
    },    
    { 
        "number"    : 0x07,
        "name"      : 'ASI_KEY_STATUS',
        "components"    : [ 
            {
                "bits"      : [7,6,5]
            },
            {
                "name"      : "UROWWRITE",
                "bit"       : 4,
                "values"    : { 
                    0 : "Unsuccess" , 
                    1 : "Success"  
                }
            },
            {
                "name"      : "NVMPROG",
                "bit"       : 3,
                "values"    : { 
                    0 : "Unsuccess" , 
                    1 : "Success"  
                }
            },
            {
                "name"      : "CHIPERASE",
                "bit"       : 2,
                "values"    : { 
                    0 : "Unsuccess" , 
                    1 : "Success"  
                }
            },
            {
                "bits"      : [1,0]
            }
        ]
    },    
    { 
        "number"        : 0x08,
        "name"          : 'ASI_RESET_REQ',
        "values"        : {
            0x00: "RUN",
            0x59: "RESET"
        }
    },    
    { 
        "number"        : 0x09,
        "name"          : 'ASI_CTRLA',
        "components"    : [
            {
                "bits"  : [7,6,5,4,3,2]
            },
            {
                "name"      : "UPDICLKSEL",
                "mask"      : 0b00000011,
                "values"    : {
                    0x00 : "Reserved",
                    0x01 : "16Mhz UPDI clock",
                    0x02 : "8Mhz UPDI clock",
                    0x03 : "4Mhz UPDI clock"
                }
            }
        ]
    },    
    { 
        "number"    : 0x0A,
        "name"      : 'ASI_SYS_CTRLA',
        "components"    : [
            {
                "bits"  :   [7,6,5,4,3,2]
            },
            {
                "bit"       : 1,
                "name"      : "UROWWRITE_FINAL",
            },
            {
                "bit"       : 0,
                "name"      : "CLKREQ"
            }

        ]   
    },    
    { 
        "number"    : 0x0B,
        "name"      : 'ASI_SYS_STATUS',
        "components"    : [
            {
                "bits"      : [7,6]
            },
            {
                "bit"       : 5,
                "name"      : "RSTSYS",
                "values"    : {
                    0 : "Not Reset State",
                    1 : "Reset State"
                }
            },
            
            {
                "bit"       : 4,
                "name"      : "INSLEEP",
                "values"    : {
                    0 : "Sleep Mode",
                    1 : "Not Sleep Mode"
                }
            },
            {
                "bit"       : 3,
                "name"      : "NVMPROG",
                "values"    : {
                    0 : "Can Program NVM",
                    1 : "Can't Program NVM"
                }
            },
            {
                "bit"       : 2,
                "name"      : "UROWPROG",
                "values"    : {
                    0 : "Can Program UROW",
                    1 : "Can't Program UROW"
                }
            },
            {
                "bit"       : 1
            },
            {
                "bit"       : 0,
                "name"      : "LOCKSTATUS",
                "values"    : {
                    0 : "NVM Locked",
                    1 : "NVM Not Locked"
                }
            },
        ]
    },    
    { 
        "number"    : 0x0C,
        "name"      : 'ASI_CRC_STATUS',
        "components"    : [
            {
                "bits"      : [7,5,5,4,3]
            },
            {
                "name"      : "CRC_STATUS",
                "mask"      : 0b00000111,
                "values"    : {
                    0x00 : "CRC Not Enabled",
                    0x01 : "CRC Enabled, Busy",
                    0x02 : "CRC Enabled, Done with OK signature",
                    0x03 : "Reserved",
                    0x04 : "CRC Enabled, Done with FAILED Signature",
                    0x05 : "Reserved",
                    0x06 : "Reserved",
                    0x07 : "Reserved"
                }
            }
        ]

    },
    {
        "number"    : 0x0D,
        "name"      : 'ASI_OCD_MESSAGE'
    }
]




