# saleae_updi_decoder

UPDI Protocol
Low Level Decoder for Saleae Logic 2 Software

## UPDI Protocol
The UPDI Protocol is used by MicroChip for their ATTINY Series of AVR 8 Bit Microcontrollers (among others).
It is a UART serial interface with a single wire/pin.  Both receive and transmit take turns on the same wire.

The Protocol is used for both programming the chip (which is well documented in the datasheet), as well as for OCD (On Chip Debugging).

Decoding the protocol can be a bit tricky, as it can (and often does) change bitrate while being used for debugging.  Thus I built a plugin for the Saleae Logic 2 software to decode and sync baud based on the protocol.

This analyzer then just simply outputs the data bytes.  

To analyze the full protocol I build a separate High Level Analyzer plug for Saleae Logic 2 that reads the byte stream and decodes it into the UPDI protocol nmemonics.

This was build and tested specifically for the ATTINY 1616.  It may or may not work with any other part.  I prototyped first with the Adafruit ATTINY 1616 Seesaw board, and then integrated the ATTINY1616 directly into my own PCB design.

## SAMPLES

See some samples <a href="./Samples/README.MD">here</a>.

## Hardware/Software Utilized

### Saleae Logic2 Software
<a href="https://www.saleae.com/pages/downloads"><img src="/Images/Logic2.png" width="200"></a>.

### ATTINY1616
<a href="https://www.microchip.com/en-us/product/attiny1616">
    <img src="/Images/Microchip_ATTINY1616.png" width="200"/>
</a>
<p></p>
Find the datasheet 
<a href="https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny1614-16-17-DataSheet-DS40002204A.pdf">
here</a>.

### AdaFruit
<a href="https://www.adafruit.com/product/5690">
    <img src="/Images/Adafruit_5690.jpg" width="200"/>
</a>

### Microchip PICKIT 5 In-Circuit Debugger
<a href="https://www.microchip.com/en-us/development-tool/pg164150">
    <img src="/Images/Microchip_PICKIT_5.png" width="200"/>
</a>

### Cheap Amazon.com Logic Analzer
<a href="https://www.amazon.com/gp/product/B077LSG5P2">
    <img src="/Images/Cheap_LogicAnalyzer.jpg" width="100"/>
</a>


