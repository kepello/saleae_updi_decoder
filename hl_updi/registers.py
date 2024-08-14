REGISTERS = [
    { 
        "number"    : 0x00,
        "name"      : 'STATUSA',
        "values"    : {
            "mask"      : 0b00001111
        }
    },

]


    # def CSRegister(self, number, value, direction='='):
    #     mnemonics  = ''
    #     if number == 0x00:
    #         rev = value>>4
    #         mnemonics = 'STATUSA %s 0x%02X (UPDIREV=0x%02X)' % (direction,value,rev)
    #     elif number == 0x01:
    #         mnemonics = 'STATUSB %s 0x%02X (PESIG=' % (direction,value)
    #         if value == 0x00:
    #             mnemonics += 'NO_ERROR'
    #         elif value == 0x01:
    #             mnemonics += 'PARITY_ERROR'
    #         elif value == 0x02:
    #             mnemonics += 'FRAME_ERROR'            
    #         elif value == 0x03:
    #             mnemonics += 'ACCESS_LAYER_TIMEOUT'            
    #         elif value == 0x04:
    #             mnemonics += 'CLOCK_RECOVERY_ERROR'
    #         elif value == 0x05:
    #             mnemonics += 'RESERVED'
    #         elif value == 0x06:
    #             mnemonics += 'BUS_ERROR'
    #         elif value == 0x07:
    #             mnemonics += 'CONTENTION_ERROR'
    #     elif number == 0x02:
    #         mnemonics = 'CTRLA %s 0x%02X (' % (direction,value)
    #         if (value & 0x80):
    #             mnemonics += 'IBDLY '
    #         if (value & 0x20):
    #             mnemonics += 'PARD '
    #         if (value & 0x10):
    #             mnemonics += 'DTD '
    #         if (value & 0x08):
    #             mnemonics += 'RSD '
    #         gtv = value & 0x07
    #         mnemonics += 'GTVAL='
    #         if (gtv == 0x00):
    #             mnemonics += '128_CYCLE'
    #         elif (gtv == 0x01):
    #             mnemonics += '64_CYCLE'
    #         elif (gtv == 0x02):
    #             mnemonics += '32_CYCLE'
    #         elif (gtv == 0x03):
    #             mnemonics += '16_CYCLE'
    #         elif (gtv == 0x04):
    #             mnemonics += '8_CYCLE'
    #         elif (gtv == 0x05):
    #             mnemonics += '4_CYCLE'
    #         elif (gtv == 0x06):
    #             mnemonics += '2_CYCLE'
    #         elif (gtv == 0x07):
    #             mnemonics += 'RESERVED'
    #         mnemonics += ')'
    #     elif number == 0x03:
    #         mnemonics = 'CTRLB %s 0x%02X (' % (direction,value)
    #         if (value & 0x8):
    #             mnemonics += 'NACKDIS '
    #         if (value & 0x04):
    #             mnemonics += 'CCDETDIS '
    #         if (value & 0x02):
    #             mnemonics += 'UPDIDIS'
    #         mnemonics= mnemonics.strip() + ')'
    #     elif number == 0x04:
    #         mnemonics = 'ASI_OCD_CTRLA %s 0x%02X (' % (direction, value);
    #         if (value & 0x80):
    #             mnemonics += 'SOR_DIR '
    #         if (value & 0x02): 
    #             mnemonics += 'RUN '
    #         if (value & 0x01):
    #             mnemonics += 'STOP'
    #         mnemonics= mnemonics.strip() + ')'
    #     elif number == 0x05:
    #         # Requires OCDMV
    #         mnemonics = 'ASI_OCD_STATUS %s (0x%02X (' % (direction, value);
    #         if (value & 0x10):
    #             mnemonics += 'OCDMV '
    #         if (value & 0x01):
    #             mnemonics += 'STOPPED'
    #         mnemonics = mnemonics.strip() + ')'
    #     elif number == 0x06: 
    #         mnemonics = 'RESERVED_6 %s 0x%02X' % (direction, value)    
    #     elif number == 0x07:
    #         mnemonics = 'ASI_KEY_STATUS %s 0x%02X (' % (direction,value)
    #         if (value & 0x20):
    #             mnemonics += 'UROWWRITE '
    #         if (value & 0x10):
    #             mnemonics += 'NVMPROG '
    #         if (value & 0x08):
    #             mnemonics += 'CHIPERASE'
    #         mnemonics = mnemonics.strip() + ')'
    #     elif number == 0x08:
    #         mnemonics = 'ASI_RESET_REQ %s 0x%02X (' % (direction, value)
    #         if (value == 0x00):
    #             mnemonics += 'RUN'
    #         elif (value == 0x59):
    #             mnemonics += 'RESET'
    #         else:
    #             mnemonics += 'CLEARED'
    #         mnemonics += ')'
    #     elif number == 0x09:
    #         clk = value & 0x03
    #         mnemonics = 'ASI_CTRLA %s 0x%02X (UPDICLKSEL=' % (direction, value)
    #         if (clk == 0x00):
    #             mnemonics += 'RESERVED_UPDICLK'
    #         elif (clk == 0x01):
    #             mnemonics += '16MHZ_UPDICLK'
    #         elif (clk == 0x02):
    #             mnemonics += '8MHZ_UPDICLK'            
    #         elif (clk == 0x03):
    #             mnemonics += '4MHZ_UPDICLK'
    #         mnemonics += ')'
    #     elif number == 0x0A:
    #         mnemonics = 'ASI_SYS_CTRLA %s 0x%02X (not yet described)' % (direction, value)
    #     elif number == 0x0B:
    #         mnemonics = 'ASI_SYS_STATUS %s 0x%02X (' % (direction,value)
    #         if (value & 0x80):
    #             mnemonics += 'UNKNOWN_BIT_8 '
    #         if (value & 0x40):
    #             mnemonics += 'UNKNOWN_BIT_7 '    
    #         if (value & 0x02): 
    #             mnemonics += 'UNKNOWN_BIT_2 '           
    #         if (value & 0x20):
    #             mnemonics += 'RSTSYS '
    #         if (value & 0x10):
    #             mnemonics += 'INSLEEP '
    #         if (value & 0x08):
    #             mnemonics += 'NVMPROG '
    #         if (value & 0x04):
    #             mnemonics += 'UROWPROG '
    #         if (value & 0x01):
    #             mnemonics += 'NVMLOCK '
    #         mnemonics = mnemonics.strip() + ')'
    #     elif number == 0x0C:
    #         crc = value & 0x03
    #         mnemonics = 'ASI_CRC_STATUS %s 0x%02X (CRC_STATUS=0x%02X ' % (direction,value,crc)
    #         if (crc == 1):
    #             mnemonics += 'NOT_ENABLED'
    #         elif (crc == 2):
    #             mnemonics += 'BUSY'
    #         elif (crc == 3):
    #             mnemonics += 'OK'
    #         elif (crc == 4):
    #             mnemonics += 'FAILED'
    #         else:
    #             mnemonics += 'RESERVED'
    #         mnemonics += ')'
    #     elif number == 0x0D:
    #         mnemonics = 'ASI_OCD_MESSAGE %s 0x%02X (' % (direction, value)
    #     else:
    #         mnemonics = 'UNKNOWN_CS_REGISTER %s 0x%02X' % (direction, value)
    #     return mnemonics




