from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, ChoicesSetting
from enum import IntEnum, Enum
from opcodes import OPCODES


class States(Enum):
    Start =     1
    Opcode = 2
    Address =   3
    Data =      4
    Repeat =    5
    Ack =       6

class DataArray(list):

    def toHexString(self, isSpace=False):
        hex = '0x'
        for item in self:
            if (isSpace==True):
                hex += '%02X ' % item
            else:
                hex += '%02X' % item
        return hex.strip()
    
    def toAsciiString(self):
        ascii = '"'
        for item in self:
            ascii+=chr(item)
        ascii += '"'
        return ascii
    
    def toTotal(self):
        total = 0
        for item in self:
            total = (total << 8) + item
        return total

        
# High level analyzers must subclass the HighLevelAnalyzer class.
class hla(HighLevelAnalyzer):

    DisplayHex = ChoicesSetting(['No', 'Yes'])

    # Result Types supported
    result_types = {
        'UPDI': {
            'format' : '{{data.command}}'
        }
    }

    def __init__(self):

        self.state = States.Start

        self.start_time = 0  
        self.mnemonic = ''
        self.payload:DataArray = DataArray()
        self.opcode_start = 0
        self.frames = []
        self.has_ack = False
        self.address_count=0
        self.data_count=0
        self.key_count=0
        self.repeat_count= 0
        self.recognized_opcode = None
        self.comments = []

    def gethex(self):
        h = self.payload.toHexString(isSpace=True)
        self.opcode_start += len(self.payload)
        self.payload = DataArray()
        return h
    
    def address_size(self, address_part, byte):
        value = (byte & 0b1100) >> 2 if (address_part == "A") else (byte & 0b0011)
        if (value == 0x00):
            return 1 # (1,'Byte')
        elif (value == 0x01):
            return 2 #(2,'Word')
        elif (value == 0x02):
            return 3 #(3,'3 Bytes')
        else:
            return 4 #(0,'Reserved')    

    def data_size(self, address_part, byte):
        if (address_part == '1'):
            return 1
        else:
            value = (byte & 0b0011)
            if (value == 0x00):
                return 1 #(1,'Byte')
            elif (value == 0x01):
                return 2 # (2,'Word')
            else:
                return 0 #(0,'Reserved') 
    
    def key_size(self, byte):
        value = (byte & 0b11)
        if (value == 0x00):
            return 8 
        elif (value == 0x01):
            return 16 
        elif (value == 0x02):
            return 32
        else:
            return 32   # 0x03 is Described as RESERVED in the documentation, observation shows a 32 byte result
        
    def register_info(self, byte):
        return(byte & 0b1111)

    def addframe(self, mnemonic, end_time, comments=[]):     
        # Display the Frame
        hex = self.gethex()
        self.frames.append(AnalyzerFrame('UPDI', self.start_time, end_time, {
            'count' : '%04X' % self.opcode_start,
            'data' : hex,
            'command' : mnemonic,
            'comments' : ', '.join(comments) if len(comments)>0 else ''
        }))

    # Decode function, called by Logic 2 software for each byte
    def decode(self, frame:AnalyzerFrame):

        # Initialize our results array
        self.frames=[]

        # Preserve any comments from ll analyzer
        if ('comments' in frame.data):
            self.comments.append(frame.data['comments'])

        # Process if there is data
        if ('data' in frame.data):
            byte = frame.data['data'][0]
            self.payload.append(byte)
        else:
            return self.frames
        
        # Start State = beginning of new command
        if (self.state == States.Start):

            # Handle special events
            if (byte == 0x55):
                # SYNC event
                self.comments.append('(SYNC)')
                self.start_time = frame.start_time
                return self.frames
            elif (byte == 0xFF):
                # IDLE event
                self.comments.append('(IDLE)')
                self.start_time = frame.start_time
                return self.frames
            else:
                # Standard Data
                if (self.start_time == 0):
                    self.start_time = frame.start_time
        
            self.address = DataArray()
            self.data = DataArray()
            self.recognized_opcode = None

            # Determine which opcode we are processing
            for code in OPCODES:
                if (byte & code['mask']) == code['value']:
                    # Matched code from list
                    self.recognized_opcode = code.copy()
                    # What additional information does this opcode require
                    if ('address' in code):
                        self.address_count = self.address_size(code['address'], byte)
                    if ('data' in code):
                        self.data_count = self.data_size(code['data'],byte)
                    if ('key' in code):
                        self.data_count = self.key_size(byte)
                    if ('register' in code):
                        self.cs = self.register_info(byte)                    
                    self.state = States.Address
                    break

            # Now we gather the remaining data about the opcode 
            if self.recognized_opcode != None:
                self.state = States.Address
            else:
                self.addframe('INVALID_OPCODE %02X' % byte, frame.end_time)
                
        # If there is an address, we process it first
        if (self.state == States.Address):
            if (self.address_count != 0):
                self.address.append(byte)
                self.address_count -= 1
            if self.address_count == 0:
                self.state = States.Data
                return self.frames

        # Next we process any data 
        if (self.state == States.Data):
            if (self.data_count != 0):
                self.data.append(byte)
                self.data_count -= 1
            if self.data_count == 0:

                self.mnemonic += self.recognized_opcode['name']

                if ('operator' in self.recognized_opcode) and (self.recognized_opcode['operator']=='*'):
                    # Data value only, REPEAT
                    self.mnemonic += ' %s %s' % (self.recognized_opcode['operator'], self.data.toHexString())
                    self.repeat_count = self.data.toTotal()
                elif ('register' in self.recognized_opcode):
                    # Register operation (LDCS, STCS operation data)
                    self.mnemonic += ' 0x%02X %s %s' % (self.cs, self.recognized_opcode['operator'], self.data.toHexString())
                elif ('address' in self.recognized_opcode) and not ('data' in self.recognized_opcode):
                    # Setting Pointer to Address (LD, ST)
                    self.mnemonic += ' %s %s' % (self.recognized_opcode['operator'], self.address.toHexString())
                elif ('data' in self.recognized_opcode) and not ('address' in self.recognized_opcode):
                    # Data to address (ptr)
                    self.mnemonic += ' %s %s' % (self.recognized_opcode['operator'], self.data.toHexString())
                elif ('key' in self.recognized_opcode) and (self.recognized_opcode['operator'] == '='):
                    # Setting KEY
                    self.mnemonic += ' KEY %s %s' % (self.recognized_opcode['operator'], self.data.toAsciiString())
                elif ('key' in self.recognized_opcode) and (self.recognized_opcode['operator'] == '=='):
                    # Getting SIB
                    self.mnemonic += ' SIB %s %s' % (self.recognized_opcode['operator'], self.data.toAsciiString())
                elif ('data' in self.recognized_opcode) and ('address' in self.recognized_opcode):
                    # Address and data (LDS, STS)
                    self.mnemonic += ' %s %s %s' % (self.address.toHexString(),self.recognized_opcode['operator'] , self.data.toHexString())
                
                if (self.recognized_opcode['name']!='REPEAT') and (self.repeat_count > 0):
                    self.comments.append('(%d repeat(s) left)' % (self.repeat_count-1))
                self.addframe(self.mnemonic, frame.end_time, self.comments)
                self.mnemonic = ''
                self.comments = []
                self.start_time = 0

                # Are we repeating?  (We don't repeat the repeat command itself)
                if (self.recognized_opcode['name']!='REPEAT') and (self.repeat_count > 0):
                    # We finished a repeat
                    self.repeat_count -= 1
                    if (self.repeat_count > 0):
                        # We need to repeat this command again
                        # We start next cycle with command alread recognized, ready to process address, data, etc
                        self.state = States.Address
                        self.address = DataArray()
                        self.data = DataArray()
                    else:
                        self.state = States.Start
                else:
                    self.state = States.Start

        return self.frames
    


    # def old_decode(self, frame: AnalyzerFrame):

    #     self.frames = []
    #     if ('data' in frame.data):
    #         b = frame.data['data'][0]
    #         self.payload.append(b)
    #         if (self.start_time == 0):
    #             self.start_time = frame.start_time

    #         if (self.state == States.Start):
    #             self.start_time = frame.start_time
    #             self.data = DataArray()
    #             self.address = DataArray()
    #             # if (b == Codes.BREAK):
    #             #     self.breakcode(frame)
    #             # if (b & 0b00010000):
    #             #     self.error(frame)
    #             # else:
    #             self.code(b)
    #             self.last_code = b
    #             return self.frames

    #         if (self.state == States.Address):
    #             if (self.addressLength != 0):
    #                 self.address.append(b)
    #                 self.addressLength -= 1
    #             if self.addressLength == 0:
    #                 self.state = States.Data
    #                 return self.frames

    #         if (self.state == States.Data):
    #             if (self.dataLength != 0):
    #                 self.data.append(b)
    #                 self.dataLength -= 1
    #             if self.dataLength == 0:
    #                 self.endtime = frame.end_time
    #                 self.complete()
                    
    #                 if (self.repeatCount>0):
    #                     self.repeatCode = self.last_code
    #                 if (self.hasAck):
    #                     print('*** requires ACK')
    #                     self.state = States.ACK
    #                     return self.frames
    #                 else:
    #                     self.state = States.Repeat

    #         if (self.state == States.ACK):
    #             if (b == Codes.ACK):
    #                 self.code(Codes.ACK)
    #             self.state = States.Repeat

    #         if (self.state == States.Repeat):
    #             # Do we need to repeat this command?
    #             if self.command != Opcodes.REPEAT:
    #                 if (self.repeatCount>0):
    #                     print('*** requires a repeat')
    #                     self.start_time = 0
    #                     self.data = DataArray()
    #                     self.address = DataArray()
    #                     self.code(self.repeatCode)
    #                     self.repeatCount -= 1
    #                 else:
    #                     self.state = States.Start
    #             else:
    #                 self.state = States.Start
            
    #     return self.frames

    # def error(self, frame):
    #     hex = self.gethex()
    #     b = frame.data['data'][0]
    #     mnemonics = 'ERROR 0x%02X' % b
    #     print(mnemonics, hex)
    #     self.endtime = frame.end_time
    #     self.addframe(mnemonics, self.byteStart, hex)

    # def breakcode(self, frame: AnalyzerFrame):
    #     self.repeatCount = 0
    #     self.repeatCode = 0
    #     hex = self.gethex()
    #     mnemonics = 'BREAK'
    #     print(mnemonics)
    #     self.endtime = frame.end_time
    #     self.addframe(mnemonics, self.byteStart, hex)

    # # def ack(self, frame: AnalyzerFrame):
    # #     hex = self.gethex()
    # #     mnemonics = ' ACK'
    # #     print(mnemonics)
    # #     self.endtime = frame.end_time
    # #     self.addframe(mnemonics, self.byteStart, hex)

    # # def sync(self, frame: AnalyzerFrame):
    # #     hex = self.gethex()
    # #     mnemonics = 'SYNC '
    # #     # print(mnemonics)
    # #     self.endtime = frame.end_time
    # #     self.addframe(mnemonics, self.byteStart, hex)

    # def code(self, b):
    #     #debug('code 0x%02X'% b)

    #     if b == Codes.SYNC:
    #         self.mnemonics += '(SYNC) '
    #         return
    #     elif b == Codes.ACK:
    #         self.mnemonics += '  (ACK)'
    #         return
        
    #     self.hasAck = False
    #     opcode = b >> 5
    #     self.commandByte = b
    #     if opcode == Opcodes.LD:
    #         self.command=Opcodes.LD
    #         self.state = States.Data
    #         self.sizeB = (b & BitMask.B)
    #         self.dataLength = self.dataSize(self.sizeB)[0]
    #         #debug('LD 0x%02X dataLength 0x%02X' % (self.sizeB, self.dataLength))
    #     elif opcode == Opcodes.LDS:
    #         self.command = Opcodes.LDS
    #         self.state = States.Address
    #         self.sizeA = ((b & BitMask.A)>>2)
    #         self.addressLength =  self.addressSize(self.sizeA)[0]
    #         self.sizeB = ((b & BitMask.B)) 
    #         self.dataLength = self.dataSize(self.sizeB)[0]
    #         #debug('LDS ', self.addressLength, self.dataLength)
    #     elif opcode == Opcodes.STS:
    #         self.command=Opcodes.STS
    #         self.state = States.Address
    #         self.sizeA = ((b & BitMask.A)>>2) 
    #         self.addressLength = self.addressSize(self.sizeA)[0]
    #         self.sizeB = ((b & BitMask.B)>>2)
    #         self.dataLength = self.dataSize(self.sizeB)[0]
    #         self.hasAck = True
    #         print('*** setting hasAck=true')
    #         #debug('STS ', self.addressLength, self.dataLength)
    #     elif opcode == Opcodes.ST:
    #         self.command=Opcodes.ST
    #         self.state = States.Data
    #         self.sizeB = (b & BitMask.B) 
    #         self.dataLength = self.dataSize(self.sizeB)[0]
    #         self.hasAck = True
    #         print('*** setting hasAck=true')
    #         #debug('ST dataLength=0x%02X' % self.dataLength)
    #     elif opcode == Opcodes.LDCS:
    #         self.command=Opcodes.LDCS
    #         self.state = States.Data
    #         self.address.append(b & BitMask.CS)
    #         self.dataLength = 1
    #     elif opcode == Opcodes.STCS:
    #         # debug('STCS')
    #         self.command=Opcodes.STCS
    #         self.state = States.Data
    #         self.address.append(b & BitMask.CS)
    #         self.dataLength = 1
    #     elif opcode == Opcodes.REPEAT:
    #         self.command=Opcodes.REPEAT
    #         self.state = States.Data
    #         self.sizeB = (b & BitMask.B)
    #         self.dataLength = self.dataSize(self.sizeB)[0]
    #     elif opcode == Opcodes.KEY:
    #         if (b & BitMask.SIB):
    #             self.SIB = True
    #         else:
    #             self.SIB = False
    #         self.sizeB = (b & BitMask.B)
    #         self.command=Opcodes.KEY
    #         self.state = States.Data
    #         self.dataLength = self.keySize(self.sizeB)[0]


        
    # def complete(self):
    #     hex = self.gethex()
    #     #mnemonics = ''
    #     if self.command == Opcodes.KEY:
    #         self.mnemonics +=  'KEY '
    #         if (self.SIB):
    #             self.mnemonics+= 'SIB == '
    #         else:
    #             self.mnemonics+= '= '
    #         self.mnemonics += '%s:("%s")' % (
    #             self.keySize(self.sizeB)[1],
    #             self.data.toAsciiString()
    #         )

    #     elif self.command == Opcodes.ST:
    #         pointer = (self.commandByte & BitMask.A) >> 2

    #         self.mnemonics +=  'ST '
    #         if (pointer == 0x02):
    #             # Set Pointer
    #             self.mnemonics += 'PTR = %s:%s' % (
    #                 self.addressSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )
    #         elif (pointer == 0x01):
    #             # Store to incremented pointer
    #             self.mnemonics += '*(PTR++) = %s:%s' % (
    #                 self.dataSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )
    #         elif (pointer == 0x00):
    #              # Store to pointer
    #             self.mnemonics += '*(PTR) = %s:%s' % (
    #                 self.dataSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )

    #     elif self.command == Opcodes.LDCS:
    #         csreg = self.CSRegister(self.address[0],self.data[0], direction='==')
    #         self.mnemonics +=  'LDCS %s' % csreg

    #     elif self.command == Opcodes.STCS:
    #         csreg = self.CSRegister(self.address[0],self.data[0])
    #         self.mnemonics +=  'STCS %s' % csreg

    #     elif self.command == Opcodes.LD:
    #         #debug('LD sizeB 0x%02X data %s' % (self.sizeB, self.data.toHexString()))
    #         pointer = (self.commandByte & BitMask.A) >> 2
    #         self.mnemonics +=  'LD '
    #         if (pointer == 0x02):
    #             # Set Pointer
    #             self.mnemonics += 'PTR = %s:%s' % (
    #                 self.addressSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )
    #         elif (pointer == 0x01):
    #             # Store to incremented pointer
    #             self.mnemonics += '*(PTR++) == %s:%s' % (
    #                 self.dataSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )
    #         elif (pointer == 0x00):
    #              # Store to pointer
    #             self.mnemonics += '*(PTR) == %s:%s' % (
    #                 self.dataSize(self.sizeB)[1], 
    #                 self.data.toHexString()
    #             )

    #     elif self.command == Opcodes.REPEAT:
    #         # calculate value) from hex repeat count
    #         repeat = self.data
    #         self.mnemonics +=  'REPEAT %s' % repeat.toHexString()
    #         self.repeatCount = repeat.toTotal() 
    #         self.repeatCode = 0

    #     elif self.command == Opcodes.LDS:
    #         self.mnemonics += 'LDS %s:%s == (%s:%s)' % (
    #             self.addressSize(self.sizeA)[1], 
    #             self.address.toHexString(), 
    #             self.dataSize(self.sizeB)[1],
    #             self.data.toHexString()
    #         )
        
    #     elif self.command == Opcodes.STS:
    #         self.mnemonics +=  'STS %s:%s = (%s:%s)' % (
    #             self.addressSize(self.sizeA)[1],
    #             self.address.toHexString(), 
    #             self.dataSize(self.sizeB)[1],
    #             self.data.toHexString()
    #         )
    #     else:
    #         self.mnemonics +=  'UNself.RECOGNIZED_OPCODE 0x%02X' % self.command

    #     # Display to the Console, either Menomics or Descriptive based on setting
    #     print(self.mnemonics)

    #     self.addframe(self.mnemonics, self.byteStart, hex)
    #     #self.mnemonics = ''
    #     self.state = States.Start



    def MemoryMap(self, address, value, direction='='):
        if address <= 0x003F:
            register = ''
            offset = address - 0x003F
            if (offset==0x00):
                register = 'GPIOR0'
            elif (offset==0x01):
                register = 'GPIOR1'
            elif (offset==0x02):
                register = 'GPIOR2'
            elif (offset==0x03):
                register = 'GIPOR3'
            mnemonics = 'I/O Reg 0x%04X %d (0x%2X:%s)' % (address, direction, value, register)
        elif address <= 0x0FFF:
            mnemonics = 'Ext. I/O Reg 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <=0x13FF:
            mnemonics = 'NVM I/O 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <= 0x37FF:
            mnemonics = 'RESERVED 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <= 0x3FFF:
            mnemonics = 'Internal SRAM 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <= 0x7FFF:
            mnemonics = 'RESERVED 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <= 0xBFFF:
            mnemonics = 'FLASH 0x%04X %d (0x%2X)' % (address, direction, value)
        elif address <= 0xFFFF:
            mnemonics = 'RESERVED 0x%04X %d (0x%2X)' % (address, direction, value)

    def CSRegister(self, number, value, direction='='):
        mnemonics  = ''
        if number == 0x00:
            rev = value>>4
            mnemonics = 'STATUSA %s 0x%02X (UPDIREV=0x%02X)' % (direction,value,rev)
        elif number == 0x01:
            mnemonics = 'STATUSB %s 0x%02X (PESIG=' % (direction,value)
            if value == 0x00:
                mnemonics += 'NO_ERROR'
            elif value == 0x01:
                mnemonics += 'PARITY_ERROR'
            elif value == 0x02:
                mnemonics += 'FRAME_ERROR'            
            elif value == 0x03:
                mnemonics += 'ACCESS_LAYER_TIMEOUT'            
            elif value == 0x04:
                mnemonics += 'CLOCK_RECOVERY_ERROR'
            elif value == 0x05:
                mnemonics += 'RESERVED'
            elif value == 0x06:
                mnemonics += 'BUS_ERROR'
            elif value == 0x07:
                mnemonics += 'CONTENTION_ERROR'
        elif number == 0x02:
            mnemonics = 'CTRLA %s 0x%02X (' % (direction,value)
            if (value & 0x80):
                mnemonics += 'IBDLY '
            if (value & 0x20):
                mnemonics += 'PARD '
            if (value & 0x10):
                mnemonics += 'DTD '
            if (value & 0x08):
                mnemonics += 'RSD '
            gtv = value & 0x07
            mnemonics += 'GTVAL='
            if (gtv == 0x00):
                mnemonics += '128_CYCLE'
            elif (gtv == 0x01):
                mnemonics += '64_CYCLE'
            elif (gtv == 0x02):
                mnemonics += '32_CYCLE'
            elif (gtv == 0x03):
                mnemonics += '16_CYCLE'
            elif (gtv == 0x04):
                mnemonics += '8_CYCLE'
            elif (gtv == 0x05):
                mnemonics += '4_CYCLE'
            elif (gtv == 0x06):
                mnemonics += '2_CYCLE'
            elif (gtv == 0x07):
                mnemonics += 'RESERVED'
            mnemonics += ')'
        elif number == 0x03:
            mnemonics = 'CTRLB %s 0x%02X (' % (direction,value)
            if (value & 0x8):
                mnemonics += 'NACKDIS '
            if (value & 0x04):
                mnemonics += 'CCDETDIS '
            if (value & 0x02):
                mnemonics += 'UPDIDIS'
            mnemonics= mnemonics.strip() + ')'
        elif number == 0x04:
            mnemonics = 'ASI_OCD_CTRLA %s 0x%02X (' % (direction, value);
            if (value & 0x80):
                mnemonics += 'SOR_DIR '
            if (value & 0x02): 
                mnemonics += 'RUN '
            if (value & 0x01):
                mnemonics += 'STOP'
            mnemonics= mnemonics.strip() + ')'
        elif number == 0x05:
            # Requires OCDMV
            mnemonics = 'ASI_OCD_STATUS %s (0x%02X (' % (direction, value);
            if (value & 0x10):
                mnemonics += 'OCDMV '
            if (value & 0x01):
                mnemonics += 'STOPPED'
            mnemonics = mnemonics.strip() + ')'
        elif number == 0x06: 
            mnemonics = 'RESERVED_6 %s 0x%02X' % (direction, value)    
        elif number == 0x07:
            mnemonics = 'ASI_KEY_STATUS %s 0x%02X (' % (direction,value)
            if (value & 0x20):
                mnemonics += 'UROWWRITE '
            if (value & 0x10):
                mnemonics += 'NVMPROG '
            if (value & 0x08):
                mnemonics += 'CHIPERASE'
            mnemonics = mnemonics.strip() + ')'
        elif number == 0x08:
            mnemonics = 'ASI_RESET_REQ %s 0x%02X (' % (direction, value)
            if (value == 0x00):
                mnemonics += 'RUN'
            elif (value == 0x59):
                mnemonics += 'RESET'
            else:
                mnemonics += 'CLEARED'
            mnemonics += ')'
        elif number == 0x09:
            clk = value & 0x03
            mnemonics = 'ASI_CTRLA %s 0x%02X (UPDICLKSEL=' % (direction, value)
            if (clk == 0x00):
                mnemonics += 'RESERVED_UPDICLK'
            elif (clk == 0x01):
                mnemonics += '16MHZ_UPDICLK'
            elif (clk == 0x02):
                mnemonics += '8MHZ_UPDICLK'            
            elif (clk == 0x03):
                mnemonics += '4MHZ_UPDICLK'
            mnemonics += ')'
        elif number == 0x0A:
            mnemonics = 'ASI_SYS_CTRLA %s 0x%02X (not yet described)' % (direction, value)
        elif number == 0x0B:
            mnemonics = 'ASI_SYS_STATUS %s 0x%02X (' % (direction,value)
            if (value & 0x80):
                mnemonics += 'UNKNOWN_BIT_8 '
            if (value & 0x40):
                mnemonics += 'UNKNOWN_BIT_7 '    
            if (value & 0x02): 
                mnemonics += 'UNKNOWN_BIT_2 '           
            if (value & 0x20):
                mnemonics += 'RSTSYS '
            if (value & 0x10):
                mnemonics += 'INSLEEP '
            if (value & 0x08):
                mnemonics += 'NVMPROG '
            if (value & 0x04):
                mnemonics += 'UROWPROG '
            if (value & 0x01):
                mnemonics += 'NVMLOCK '
            mnemonics = mnemonics.strip() + ')'
        elif number == 0x0C:
            crc = value & 0x03
            mnemonics = 'ASI_CRC_STATUS %s 0x%02X (CRC_STATUS=0x%02X ' % (direction,value,crc)
            if (crc == 1):
                mnemonics += 'NOT_ENABLED'
            elif (crc == 2):
                mnemonics += 'BUSY'
            elif (crc == 3):
                mnemonics += 'OK'
            elif (crc == 4):
                mnemonics += 'FAILED'
            else:
                mnemonics += 'RESERVED'
            mnemonics += ')'
        elif number == 0x0D:
            mnemonics = 'ASI_OCD_MESSAGE %s 0x%02X (' % (direction, value)
        else:
            mnemonics = 'UNKNOWN_CS_REGISTER %s 0x%02X' % (direction, value)
        return mnemonics




