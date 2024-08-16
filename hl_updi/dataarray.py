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