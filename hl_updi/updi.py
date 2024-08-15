from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, ChoicesSetting
from enum import IntEnum, Enum
from opcodes import OPCODES
from registers import REGISTERS

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
        hex = self.gethex()

        # print(self.start_time, end_time, '0x%04X'% self.opcode_start, hex, mnemonic, ', '.join(comments) if len(comments)>0 else '') 

        # Display the Frame
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
                self.addframe("IDLE", frame.end_time)
                self.mnemonic = ''
                self.comments = []
                self.start_time = 0
                return self.frames
            elif (byte == 0x00):
                # BREAK event
                self.comments.append('(BREAK)')
                self.start_time = frame.start_time
                self.addframe("BREAK", frame.end_time)
                self.mnemonic = ''
                self.comments = []
                self.start_time = 0
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
            # It's possible that we are repeating a previous opcode, which would make the start
            # here rather than at the opcode point
            if (self.start_time == 0):
                self.start_time = frame.start_time
            # If we need address, get it
            if (self.address_count != 0):
                self.address.append(byte)
                self.address_count -= 1
            # If we are now done with address, move on to data
            if self.address_count == 0:
                self.state = States.Data
                return self.frames

        # Next we process any data 
        if (self.state == States.Data):
            if (self.data_count != 0):
                self.data.append(byte)
                self.data_count -= 1
            if self.data_count == 0:

                # No more data, so that means we have completed the command
                self.mnemonic += self.recognized_opcode['name']

                if ('operator' in self.recognized_opcode) and (self.recognized_opcode['operator']=='*'):
                    # Data value only, REPEAT
                    self.mnemonic += ' %s %s' % (self.recognized_opcode['operator'], self.data.toHexString())
                    self.repeat_count = self.data.toTotal()
                elif ('register' in self.recognized_opcode):
                    # Register operation (LDCS, STCS operation data)
                    self.mnemonic += ' ' + self.register(self.cs, self.recognized_opcode['operator'], self.data[0])
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
    

    # Decode the CS register names and values
    def register(self, cs, operator, data):
        
        # Defaults if no definition is found
        register_name = '(%02X) UNDEFINED ' % cs
        register_parts = []

        # Look up the register
        for register in REGISTERS:

            # See if our value matches the defined register number
            if 'number' in register and register['number'] == cs:

                # Matched, use the defiend name
                if 'name' in register:
                    register_name = '0x%02X (%s)' % (cs, register['name'])

                # Check if this register has one or more defined portions
                if 'components' in register:
                    for component in register['components']:
                        
                        # Handle groups of bits
                        if ('bits') in component:
                            for bit in component['bits']:
                                component_value = ((1 << bit) & data) >> (bit)
                                component_name = component['name'] if 'name' in component else 'Bit%d' % bit
                                register_parts.append('%s %s' % (component_name, 'on' if component_value>0 else 'off' ))

                        # Handle individual bit
                        elif ('bit' in component):
                            component_value = ((1 << component['bit']) & data) >> (component['bit'])
                            if 'values' in component:
                                component_definition = component['values'][component_value]
                            else:
                                component_definition = 'on' if component_value>0 else 'off'
                            component_name = component['name'] if 'name' in component else 'Bit%d' % component['bit']
                            register_parts.append('%s %s' % (component_name, component_definition))

                        # Handle masked amounts
                        elif ('mask' in component):
                            component_value = (data & component['mask']) >> (component['shift'] if 'shift' in component else 0)
                            if ('values' in component):
                                component_definition = component['values'][component_value]
                            else:
                                component_definition = '0x%02X' % component_value
                            component_name = component['name'] if 'name' in component else 'Unnamed Mask %02X' % component['mask']
                            register_parts.append('%s %s' % (component_name, component_definition ))

                        # Assume Full byte value
                        else:
                            component_value = data
                            component_name = component['name'] if 'name' in component else 'Register %02X' % cs
                            register_parts.append('%s 0x%02X' % (component_name, component_value ))

                break
        
        return ('%s %s 0x%02X' % (register_name, operator, data) + (' (%s)' % ', '.join(register_parts) if len(register_parts) else ''))

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
