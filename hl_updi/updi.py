from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, ChoicesSetting
from enum import IntEnum, Enum
from opcodes import OPCODES, ADDRESS_SIZE, DATA_SIZE, KEY_SIZE
from registers import REGISTERS
from dataarray import DataArray

class States(Enum):
    Start =     1
    Opcode =    2
    Address =   3
    Data =      4
    Repeat =    5
    Ack =       6
    Complete =  7

# High level analyzers must subclass the HighLevelAnalyzer class.
class hla(HighLevelAnalyzer):

    ShowUnknownBits = ChoicesSetting(['No', 'Yes'])

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
        self.pseudocode = ''
        self.payload:DataArray = DataArray()
        self.opcode_start = 0
        self.frames = []
        self.ack_check = 0
        self.address_count=0
        self.data_count=0
        self.key_count=0
        self.repeat_count= 0
        self.recognized_opcode = None
        self.comments = []
        self.unknown_bits = True if self.ShowUnknownBits == 'Yes' else False

    def addframe(self, mnemonic, pseudocode, end_time, comments=[]):    
        hex = self.payload.toHexString(isSpace=True)
        self.opcode_start += len(self.payload)
        self.payload = DataArray()

        # Display the Frame
        self.frames.append(AnalyzerFrame('UPDI', self.start_time, end_time, {
            'count' : '%04X' % self.opcode_start,
            'pseudocode' : pseudocode,
            'data' : hex,
            'command' : mnemonic,
            'comments' : ', '.join(comments) if len(comments)>0 else ''
        }))

######################################################################################### 
# Capture functions
######################################################################################### 

    def capture_start(self, byte, frame):
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
            self.addframe("IDLE", "", frame.end_time)
            self.mnemonic = ''
            self.pseudocode = ''
            self.comments = []
            self.start_time = 0
            return self.frames
        elif (byte == 0x00):
            # BREAK event
            self.comments.append('(BREAK)')
            self.start_time = frame.start_time
            self.addframe("BREAK", "", frame.end_time)
            self.mnemonic = ''
            self.pseudocode = ''
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
        self.repeat_byte = None
        self.last_opcode_byte = None
        self.state = States.Opcode

    def capture_opcode(self, byte, frame):

        # Are we repeating the last opcode?
        if self.repeat_byte != None:
            byte = self.repeat_byte

        # Look it up
        for code in OPCODES:
            if (byte & code['mask']) == code['value']:
                # Matched code from list
                self.recognized_opcode = code.copy()

        # Did we find a match?
        if (self.recognized_opcode != None):
            # Matched, what else do we need for this opcode?
            if ('address' in self.recognized_opcode):
                self.address_count = ADDRESS_SIZE[(byte & 0b1100) >> 2 if self.recognized_opcode['address'] == 'A' else (byte & 0b0011)]
            if ('data' in self.recognized_opcode):
                self.data_count = DATA_SIZE[(byte & 0b0011) if not self.recognized_opcode['data'] == '1' else 1]
            if ('key' in self.recognized_opcode):
                self.data_count = KEY_SIZE[byte & 0b11]
            if ('register' in self.recognized_opcode):
                self.cs = byte & 0b1111                  
            self.state = States.Address
        else:
            # No match
            self.addframe('INVALID_OPCODE 0x%02X' % byte, "Invalid Command 0x%02X", frame.end_time)
            self.state = States.Start
            
        self.last_opcode_byte = byte

    def capture_address(self, byte, frame):
        if (self.start_time == 0):
            self.start_time = frame.start_time
        self.ack_check = 0
        # If we need address, get it
        if (self.address_count != 0):
            self.address.append(byte)
            self.address_count -= 1
        # If we are now done with address, move on to data
        if self.address_count == 0:
            self.state = States.Data

    def capture_data(self, byte, frame):
        if (self.data_count != 0):
            self.data.append(byte)
            self.data_count -= 1
        if self.data_count == 0:
            self.ack_check = 0
            self.state = States.Ack

    def capture_ack(self, byte, frame):
        if ('ack' in self.recognized_opcode and self.recognized_opcode['ack']==True):
            if (not self.ack_check):
                self.ack_check = 1
            else:
                # We expect an ACK
                if (byte == 0x40):
                    self.comments.append('(ACK)')
                else:
                    self.comments.append('(MISSING ACK)')
                self.state = States.Complete
        else:
            self.state = States.Complete

    def complete_command(self, byte, frame):

        operator = self.recognized_opcode['operator']
        command = self.recognized_opcode['name']
        self.mnemonic += command
        self.pseudocode = command

        if command =='REPEAT':
            self.repeat_count = self.data.toTotal() + 1
            self.mnemonic += ' %s %s' % (operator, self.data.toHexString())
            self.pseudocode = 'Repeat next command %d times' % self.repeat_count
        elif command == 'LDCS' or command == 'STCS':
            name = self.register_name(self.cs)
            self.mnemonic += ' 0x%02X %s 0x%02X' % (self.cs, operator, self.data[0])
            self.pseudocode = '%s %s %s' % (name, operator, self.register_data(self.cs, self.data[0]))
        elif command == 'LD ptr' or command == 'ST ptr':
            self.mnemonic += ' %s %s' % (operator, self.address.toHexString())
            self.pseudocode = 'pointer %s %s' % (operator, self.address.toHexString())
        elif command == 'LD *(ptr)' or command == 'LD *(ptr)':
            self.mnemonic += ' %s %s' % (operator, self.data.toHexString())
            self.pseudocode = '*(ptr) % %s' % (operator,self.data.toHexString())
        elif command == 'LD *(ptr++)' or command == 'ST *(ptr++)':
            self.mnemonic += ' %s %s' % (operator, self.data.toHexString())
            self.pseudocode = '*(pointer++) %s %s' % (operator, self.data.toHexString())
        elif command == 'KEY':
            self.mnemonic += ' KEY %s %s' % (operator, self.data.toAsciiString())
            self.pseudocode = 'KEY %s %s' % (operator, self.data.toAsciiString())
        elif command == 'KEY SIB':
            self.mnemonic += ' SIB %s %s' % (operator, self.data.toAsciiString())
            self.pseudocode = 'SIB %s %s' % (operator, self.data.toAsciiString())
        elif command == 'LDS' or command == 'STS':
            self.mnemonic += ' %s %s %s' % (self.address.toHexString(), operator , self.data.toHexString())
            self.pseudocode = '*(%s) %s %s' % (self.address.toHexString(), operator, self.data.toHexString())
        else: 
            self.mnemonic += 'UNKNOWN COMMAND'
                
        if (command!='REPEAT') and (self.repeat_count > 0):
            self.comments.append('(%d repeat(s) left)' % (self.repeat_count-1))

        self.addframe(self.mnemonic, self.pseudocode, frame.end_time, self.comments)
        
        self.mnemonic = ''
        self.comments = []
        self.start_time = 0

######################################################################################### 
# Main DECODE Routine
######################################################################################### 

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
            self.capture_start(byte, frame)
            if (self.state == States.Start):
                return self.frames
        
        while True:
        
            # Process the Opcode 
            if (self.state == States.Opcode):
                self.capture_opcode(byte, frame)
                return self.frames

            # Process an Address, if required
            if (self.state == States.Address):
                self.capture_address(byte, frame)
                if (self.state == States.Address):
                    return self.frames

            # Process any Data, if required
            if (self.state == States.Data):            
                self.capture_data(byte, frame)
                if (self.state == States.Data):
                    return self.frames
            
            # Look for an ACK if expected
            if (self.state == States.Ack):
                self.capture_ack(byte, frame)
                if (self.state == States.Ack):
                    return self.frames
            
            # Complete this command
            if (self.state == States.Complete):
                self.complete_command(byte, frame)

                # Are we repeating?  (We don't repeat the REPEAT command itself)
                if (self.recognized_opcode['name']!='REPEAT') and (self.repeat_count > 0):
                    # We finished a repeat
                    self.repeat_opcode = self.recognized_opcode
                    self.repeat_count -= 1
                    if (self.repeat_count > 0):
                        # We need to repeat this command again
                        # We start next cycle with command alread recognized, ready to process address, data, etc
                        self.address = DataArray()
                        self.data = DataArray()
                        self.state = States.Opcode
                        self.repeat_byte = self.last_opcode_byte
                    else:
                        self.state = States.Start
                        break
                else:
                    self.state = States.Start
                    break

        return self.frames 

######################################################################################### 
# Register Decoding
######################################################################################### 

    def register_definition(self, cs):

        # Look up the register
        for register in REGISTERS:
            # See if our value matches the defined register number
            if 'number' in register and register['number'] == cs:
                return register
        return None

    def register_name(self, cs):
        register = self.register_definition(cs)
        return register['name'] if 'name' in register else ''

    # Decode the CS register names and values
    def register_data(self, cs, data):
        
        register_parts = []

        # Defaults if no definition is found
        register = self.register_definition(cs)
        if (register != None):

            # Matched, use the defiend name
            if 'name' in register:
                register_name = '0x%02X (%s)' % (cs, register['name'])

            # Check if this register has one or more defined portions
            if 'components' in register:
                for component in register['components']:
                    
                    # Handle groups of bits
                    if 'bits' in component and self.unknown_bits==True:
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
                if ('values' in register):
                    component_definition = register['values'][data]
                else:
                    component_definition = '0x%02X' % data
                component_name = register['name'] if 'name' in register else 'Register %02X' % cs
                register_parts.append('%s %s' % (component_name, component_definition ))

        return (' ,'.join(register_parts))

######################################################################################### 
# Memory Decoding
######################################################################################### 

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
