from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, ChoicesSetting
from enum import IntEnum, Enum

class Codes(IntEnum):
    BREAK =   0x00
    SYNC =   0x55
    ACK =    0x40

class Opcodes(IntEnum):
    LDS =    0b0000
    LD  =    0b0001
    STS =    0b0010
    ST =     0b0011
    LDCS =   0b0100
    REPEAT = 0b0101
    STCS =   0b0110
    KEY =    0b0111

class BitMask(IntEnum):
    Opcode = 0b11100000
    A =      0b00001100
    B =      0b00000011
    CS =     0b00001111
    SIB =    0b00000100

class States(Enum):
    Start =        1
    Address =       2
    Data =         4
    Repeat =        5

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
        ascii = ''
        for item in self:
            ascii+=chr(item)
        return ascii
    
    def toTotal(self):
        total = 0
        for item in self:
            total = (total << 8) + item
        return total


# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):

    DisplayHex = ChoicesSetting(['No', 'Yes'])

    # Result Types supported
    result_types = {
        'mnemonics': {
            'format' : '{{data.command}}'
        }
    }

    def __init__(self):

        self.state = States.Start

        self.start_time = 0  
        self.addressLength = 0
        self.dataLength = 0
        self.address:DataArray = DataArray()
        self.data:DataArray = DataArray()
        self.command = None
        self.commandByte = None
        self.payload:DataArray = DataArray()
        self.byteStart = 0
        self.SIB = False
        self.repeatCount = 0
        self.lastCode = 0
        self.sizeA = 0
        self.sizeB = 0  
        self.endtime = None
        self.frames = []

    def dumphex(self):
        
        if (self.DisplayHex=='Yes'):
            h = '0x%04X : %s' % (self.byteStart,self.payload.toHexString(isSpace=True))
            print (h)
            print ('         ',end='')
        self.byteStart += len(self.payload)
        self.payload = DataArray()

    def decode(self, frame: AnalyzerFrame):

        self.frames = []
        if ('data' in frame.data):
            b = frame.data['data'][0]
            self.payload.append(b)

            if (self.start_time == 0):
                self.start_time = frame.start_time

            if (self.state == States.Start):
                #debug('start')
                self.start_time = frame.start_time
                self.data = DataArray()
                self.address = DataArray()
                if (b == Codes.BREAK):
                    self.breakcode(frame)
                elif (b == Codes.SYNC):
                    self.sync(frame)
                elif (b == Codes.ACK):
                    self.ack(frame)
                elif (b & 0b00010000):
                    self.error(frame)
                else:
                    self.code(b)
                    self.lastCode = b
                    return self.frames

            if (self.state == States.Address):
                #debug('address addressLength 0x%02X = 0x%02X',(self.addressLength,b))
                if (self.addressLength != 0):
                    self.address.append(b)
                    self.addressLength -= 1
                if self.addressLength == 0:
                    #debug('address', self.address)
                    self.state = States.Data

            if (self.state == States.Data):
                #debug('data dataLength 0x%02X = 0x%02X' % (self.dataLength, b))
                if (self.dataLength != 0):
                    self.data.append(b)
                    self.dataLength -= 1
                if self.dataLength == 0:
                    #debug('data', self.data)
                    self.endtime = frame.end_time
                    self.complete()
                    # Do we need to repeat this command?
                    if self.command != Opcodes.REPEAT:
                        if (self.repeatCount>0):
                            self.start_time = 0
                            self.data = DataArray()
                            self.address = DataArray()
                            self.code(self.lastCode)
                            self.repeatCount -= 1
            
        return self.frames

    def error(self, frame):
        self.dumphex()
        b = frame.data['data'][0]
        mnemonics = 'ERROR 0x%02X' % b
        print(mnemonics)
        self.endtime = frame.end_time
        self.addframe(mnemonics)

    def breakcode(self, frame: AnalyzerFrame):
        self.repeatCount = 0
        self.repeatCode = 0
        self.dumphex()
        mnemonics = 'BREAK'
        print(mnemonics)
        self.endtime = frame.end_time
        self.addframe(mnemonics)

    def ack(self, frame: AnalyzerFrame):
        self.dumphex()
        mnemonics = 'ACK'
        print(mnemonics)
        self.endtime = frame.end_time
        self.addframe(mnemonics)

    def sync(self, frame: AnalyzerFrame):
        # self.dumphex()
        mnemonics = 'SYNC'
        # print(mnemonics)
        self.endtime = frame.end_time
        self.addframe(mnemonics)

    def code(self, b):
        #debug('code 0x%02X'% b)
        opcode = b >> 5
        self.commandByte = b
        if opcode == Opcodes.LD:
            self.command=Opcodes.LD
            self.state = States.Data
            self.sizeB = (b & BitMask.B)
            self.dataLength = self.dataSize(self.sizeB)[0]
            #debug('LD 0x%02X dataLength 0x%02X' % (self.sizeB, self.dataLength))
        elif opcode == Opcodes.LDS:
            self.command = Opcodes.LDS
            self.state = States.Address
            self.sizeA = ((b & BitMask.A)>>2)
            self.addressLength =  self.addressSize(self.sizeA)[0]
            self.sizeB = ((b & BitMask.B)) 
            self.dataLength = self.dataSize(self.sizeB)[0]
            #debug('LDS ', self.addressLength, self.dataLength)
        elif opcode == Opcodes.STS:
            self.command=Opcodes.STS
            self.state = States.Address
            self.sizeA = ((b & BitMask.A)>>2) 
            self.addressLength = self.addressSize(self.sizeA)[0]
            self.sizeB = ((b & BitMask.B)>>2)
            self.dataLength = self.dataSize(self.sizeB)[0]
            #debug('STS ', self.addressLength, self.dataLength)
        elif opcode == Opcodes.ST:
            self.command=Opcodes.ST
            self.state = States.Data
            self.sizeB = (b & BitMask.B) 
            self.dataLength = self.dataSize(self.sizeB)[0]
            #debug('ST dataLength=0x%02X' % self.dataLength)
        elif opcode == Opcodes.LDCS:
            self.command=Opcodes.LDCS
            self.state = States.Data
            self.address.append(b & BitMask.CS)
            self.dataLength = 1
        elif opcode == Opcodes.STCS:
            # debug('STCS')
            self.command=Opcodes.STCS
            self.state = States.Data
            self.address.append(b & BitMask.CS)
            self.dataLength = 1
        elif opcode == Opcodes.REPEAT:
            self.command=Opcodes.REPEAT
            self.state = States.Data
            self.sizeB = (b & BitMask.B)
            self.dataLength = self.dataSize(self.sizeB)[0]
        elif opcode == Opcodes.KEY:
            if (b & BitMask.SIB):
                self.SIB = True
            else:
                self.SIB = False
            self.sizeB = (b & BitMask.B)
            self.command=Opcodes.KEY
            self.state = States.Data
            self.dataLength = self.keySize(self.sizeB)[0]

    def addressSize(self,value):
        if (value == 0x00):
            return (1,'Byte')
        elif (value == 0x01):
            return (2,'Word')
        elif (value == 0x02):
            return (3,'3 Bytes')
        else:
            return (0,'Reserved')    

    def dataSize(self,value):
        if (value == 0x00):
            return (1,'Byte')
        elif (value == 0x01):
            return (2,'Word')
        else:
            return (0,'Reserved') 
    
    def keySize(self, value):
        if (value == 0x00):
            return (8, '8 Bytes')
        elif (value == 0x01):
            return (16, '16 Bytes')
        elif (value == 0x02):
            return (32, '32 Bytes')
        else:
            return (0,'Reserved')
        
    def complete(self):

        self.dumphex()

        mnemonics = ''
        if self.command == Opcodes.KEY:
            mnemonics = 'KEY '
            if (self.SIB):
                mnemonics+= 'SIB == '
            else:
                mnemonics+= '= '
            mnemonics += '%s:("%s")' % (
                self.keySize(self.sizeB)[1],
                self.data.toAsciiString()
            )

        elif self.command == Opcodes.ST:
            pointer = (self.commandByte & BitMask.A) >> 2

            mnemonics = 'ST '
            if (pointer == 0x02):
                # Set Pointer
                mnemonics += 'PTR = %s:%s' % (
                    self.addressSize(self.sizeB)[1], 
                    self.data.toHexString()
                )
            elif (pointer == 0x01):
                # Store to incremented pointer
                mnemonics += '*(PTR++) = %s:%s' % (
                    self.dataSize(self.sizeB)[1], 
                    self.data.toHexString()
                )
            elif (pointer == 0x00):
                 # Store to pointer
                mnemonics += '*(PTR) = %s:%s' % (
                    self.dataSize(self.sizeB)[1], 
                    self.data.toHexString()
                )

        elif self.command == Opcodes.LDCS:
            csreg = self.CSRegister(self.address[0],self.data[0], direction='==')
            mnemonics = 'LDCS %s' % csreg

        elif self.command == Opcodes.STCS:
            csreg = self.CSRegister(self.address[0],self.data[0])
            mnemonics = 'STCS %s' % csreg

        elif self.command == Opcodes.LD:
            #debug('LD sizeB 0x%02X data %s' % (self.sizeB, self.data.toHexString()))
            pointer = (self.commandByte & BitMask.A) >> 2
            mnemonics = 'LD '
            if (pointer == 0x02):
                # Set Pointer
                mnemonics += 'PTR = %s:%s' % (
                    self.addressSize(self.sizeB)[1], 
                    self.data.toHexString()
                )
            elif (pointer == 0x01):
                # Store to incremented pointer
                mnemonics += '*(PTR++) == %s:%s' % (
                    self.dataSize(self.sizeB)[1], 
                    self.data.toHexString()
                )
            elif (pointer == 0x00):
                 # Store to pointer
                mnemonics += '*(PTR) == %s:%s' % (
                    self.dataSize(self.sizeB)[1], 
                    self.data.toHexString()
                )

        elif self.command == Opcodes.REPEAT:
            # calculate value) from hex repeat count
            repeat = self.data
            mnemonics = 'REPEAT %s' % repeat.toHexString()
            self.repeatCount = repeat.toTotal() 
            self.repeatCode = 0

        elif self.command == Opcodes.LDS:
            mnemonics += 'LDS %s:%s == (%s:%s)' % (
                self.addressSize(self.sizeA)[1], 
                self.address.toHexString(), 
                self.dataSize(self.sizeB)[1],
                self.data.toHexString()
            )
        
        elif self.command == Opcodes.STS:
            mnemonics = 'STS %s:%s = (%s:%s)' % (
                self.addressSize(self.sizeA)[1],
                self.address.toHexString(), 
                self.dataSize(self.sizeB)[1],
                self.data.toHexString()
            )
        else:
            mnemonics = 'UNRECOGNIZED_OPCODE 0x%02X' % self.command

        # Display to the Console, either Menomics or Descriptive based on setting
        print(mnemonics)

        self.addframe(mnemonics)

    def addframe(self, mnemonics):     
        # Display the Frame
        self.frames.append(AnalyzerFrame('mnemonics', self.start_time, self.endtime, {
            'command' : mnemonics, 
        }))
        self.state = States.Start

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




