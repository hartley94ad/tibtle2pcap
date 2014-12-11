#!/usr/bin/env python
# tibtle2pcap: Read a Bluetooth Low Energy packet capture savefile generated by
# the TI Packet Sniffer utility (.psd file, but not PhotoShop), and convert it
# to a libpcap packet capture file.  The libpcap packet capture file is formatted
# to use the PPI DLT, with DLT_USER set so the BTLE Wireshark plugin can be used
# to decode the BTLE traffic.
#
# You can download the SmartRF Packet Sniffer software here:
#    http://www.ti.com/tool/packet-sniffer
# The CC2540 USB Evaluation Kit USB dongle that captures Bluetooth LE
# traffic (and injects) with default firmware is available from digikey.com
# and many other sites for $50 with the part number CC2540EMK-USB.
#
# Many thanks to Mike Ryan for blazing the path forward to open up Bluetooth LE
# sniffing and traffic analysis.
# Joshua Wright, 2014-03-03 

import struct
import sys
import pcapdump
TIRECLEN=271
DLT_PPI=192

def chan2mhz(chan):
	chanmap = {
		37:2402,  0:2404,  1:2406,  2:2408,  3:2410,  4:2412,  5:2414,  6:2416,  7:2418, 
		 8:2420,  9:2422, 10:2424, 38:2426, 11:2428, 12:2430, 13:2432, 14:2434, 15:2436,
		16:2438, 17:2440, 18:2442, 19:2444, 20:2446, 21:2448, 22:2450, 23:2452, 24:2454,
		25:2456, 26:2458, 27:2460, 28:2462, 29:2464, 30:2466, 31:2468, 32:2470, 33:2472,
		34:2474, 35:2476, 36:2478, 39:2480 }
	try:
		return chanmap[chan]
	except IndexError:
		return 0

if len(sys.argv) < 3:
	print "tibtle2pcap.py [TI psd file] [pcapfile]"
	sys.exit(1)

capfile = open(sys.argv[1], "rb")
capturedata = capfile.read()
capfile.close()

pd = pcapdump.PcapDumper(DLT_PPI, sys.argv[2])

# Chunk packet content into generator
packets=(capturedata[i:i+TIRECLEN] for i in xrange(0, len(capturedata), TIRECLEN))

for packet in packets:
	(pinfo, pnum, pts, plen) = struct.unpack('<cidh',packet[0:15])
	if pinfo != "\x01": continue 	# Bit 0 format is all we can handle
	data = packet[16:16+plen]
	payload = data[0:-3]

	# Based on my analysis of the TI Packet Sniffer savefile, we can get these
	# additional values too.  When the PPI format is updated to accommodate non-802.11
	# types, we can add them.
	rssi = ord(data[-3:-2])
	exflags = ord(data[-2:-1])
	channel=exflags&0x7f
	fcsok=(exflags&0x80 > 0)
	
	#print "Packet",pnum,"RSSI",rssi,"Channel",channel,"FCSOK",fcsok
	#hexdump.hexdump(payload)
	# This hideoous string is a PPI header with DLT_USER specified so we can use
	# the btle plugin with Wireshark.
	pd.pcap_dump("\x00\x00\x08\x00\x93\x00\x00\x00" + payload)
print
