from __future__ import print_function
import spidev
import time

#GD25Q32C
#Each DEVICE has, Each BLOCK has, Each SECTOR has, Each PAGE has
#     4M               64/32K          4K               256        BYTES
#    16K              256/128          16                -         PAGES
#    1024              16/8            -                 -         SECTORS
#    64/128               -            -                 -         BLOCKS

# There are 2 possible BLOCK sizes: 32k and 64k BYTES, there are 2 separate commands for each block size
# A 32k block has 15bits of address, a 64k block has 16bits.
# I recommend using 16bit addresses for each block, 64 total blocks 6 + 16 = 22 address bits total
# Therefore 64 blocks in device, 16 sectors in a block, 16 pages in a sector, 256 bytes in a page

class gd25q32c:
	spi = None
	#                                         Byte_1  Byte_2   Byte_3   Byte_4  Byte_5  Byte_6      n-Bytes  
	CMD_Write_Enable                 = 0x06
	CMD_Write_Disable                = 0x04
	CMD_Volatile_SR_Write_Enable     = 0x50
	CMD_Read_Status_Register_1       = 0x05 # (S7-S0)                                       (continuous)
	CMD_Read_Status_Register_2       = 0x35 # (S15-S8)                                      (continuous)
	CMD_Read_Status_Register_3       = 0x15 # (S23-S16)                                     (continuous)
	CMD_Write_Status_Register_1      = 0x01 # (S7-S0)
	CMD_Write_Status_Register_2      = 0x31 # (S15-S8)
	CMD_Write_Status_Register_3      = 0x11 # (S23-S16)
	CMD_Read_Data                    = 0x03 # A23-A16  A15-A8   A7-A0   (D7-D0) (Next byte) (continuous)
	CMD_Fast_Read                    = 0x0B # A23-A16  A15-A8   A7-A0   dummy   (D7-D0)     (continuous)
	CMD_Dual_Output_Fast_Read        = 0x3B # A23-A16  A15-A8   A7-A0   dummy   (D7-D0)     (continuous)
	CMD_Dual_IO_Fast_Read            = 0xBB # A23-A8   A7-A0,M7-M0 (D7-D0) Next byte Next byte (continuous)
	CMD_Quad_Output_Fast_Read        = 0x6B # A23-A16  A15-A8   A7-A0   dummy   (D7-D0)     (continuous)
	CMD_Quad_IO_Fast_Read            = 0xEB # A23-A0,M7-M0 dummy (D7-D0) Next byte Next byte (continuous)
	CMD_Quad_IO_Word_Fast_Read       = 0xE7 # A23-A0,M7-M0 dummy (D7-D0) Next byte Next byte (continuous)
	CMD_Continuous_Read_Mode_Reset   = 0xFF
	CMD_Page_Program                 = 0x02 # A23-A16  A15-A8   A7-A0   (D7-D0) Next byte    continuous
	CMD_Quad_Page_Program            = 0x32 # A23-A16  A15-A8   A7-A0   (D7-D0) Next byte    continuous
	CMD_Fast_Page_Program            = 0xF2 # A23-A16  A15-A8   A7-A0   (D7-D0) Next byte    continuous
	CMD_Sector_Erase                 = 0x20 # A23-A16  A15-A8   A7-A0
	CMD_Block_Erase_32K              = 0x52 # A23-A16  A15-A8   A7-A0
	CMD_Block_Erase_64K              = 0xD8 # A23-A16  A15-A8   A7-A0
	CMD_Chip_Erase                   = 0x60 # <<-- command 0xC7 can also be used <<
	CMD_Enable_Reset                 = 0x66
	CMD_Reset                        = 0x99
	CMD_Program_Erase_Suspend        = 0x75
	CMD_Program_Erase_Resume         = 0x7A
	CMD_Deep_Power_Down              = 0xB9
	CMD_Manufacturer_Device_ID       = 0x90 #  0x00    0x00     0x00   (MID7-MID0) (DID7-DID0) (continuous)
	CMD_Manufacturer_Device_ID_DUAL  = 0x92 # A23-A8   A7-A0,M7-M0 MID7-MID0,DID7-DID0        (continuous)
	CMD_Manufacturer_Device_ID_QUAD  = 0x94 # A23-A0,M7-M0 dummy,MID7-MID0,DID7-DID0          (continuous)
	CMD_Read_Unique_ID               = 0x4B # 0x00     0x00     0x00    dummy   (UID7-UID0) (continuous)
	CMD_High_Performance_Mode        = 0xA3 # dummy    dummy    dummy
	CMD_Read_Serial_Flash_Disc_Param = 0x5A # A23-A16  A15-A8   A7-A0   dummy       (D7-D0) (continuous)
	CMD_Read_Identification          = 0x9F # (MID7-M0) (JDID15-JDID8) (JDID7-JDID0)        (continuous)
	CMD_Erase_Security_Registers     = 0x44 # A23-A16  A15-A8   A7-A0
	CMD_Program_Security_Registers   = 0x42 # A23-A16  A15-A8   A7-A0   (D7-D0) (D7-D0)      continuous
	CMD_Read_Security_Registers      = 0x48 # A23-A16  A15-A8   A7-A0   dummy (D7-D0)       (continuous)
	CMD_Release_From_Deep_Power_Down_And_Read_Device_ID = 0xAB # dummy  dummy dummy (DID7-DID0) (continuous)
	CMD_Release_From_Deep_Power_Down = 0xAB
	
	BLOCK_size_64k_addr              = 0x010000 #  64 blocks  in a device
	BLOCK_size_32k_addr              = 0x008000 # 128 blocks  in a device
	SECTOR_size_addr                 = 0x001000 #  1k sectors in a device
	PAGE_size_addr                   = 0x000100 # 16k pages   in a device
	
	NUM_BLOCKS_size_64k              = 64    #  64 blocks  in a device
	NUM_BLOCKS_size_32k              = 128   # 128 blocks  in a device
	NUM_SECTORS                      = 1024  #  1k sectors in a device
	NUM_PAGES                        = 16384 # 16k pages   in a device
	
	# Constructor
	def __init__(self, spi_device=0, spi_channel=0, max_speed_hz = 1000000, debug=False): # 1MHz
		self.spi              = spidev.SpiDev(spi_device, spi_channel)
		self.spi.max_speed_hz = max_speed_hz
		self.debug            = debug

	def write_enable(self, debug=False):
		if (debug or self.debug):
			print("----> write_enable called <----")
		self.spi.xfer2([self.CMD_Write_Enable])
#		if (self.check_wip_and_wel(expected_status=0x02, timestep = 0.00001, debug=debug) == 0):
		if ((self.read_status_register_1() & 0x03) == 0x02):
			if (debug or self.debug):
				print("SUCCESSFUL write_enable")
			return 0
		else:
			print("ERROR, did not see WIP clear and WEL set from write_enable")
			return -1
	
	def write_disable(self, debug=False):
		if (debug or self.debug):
			print("----> write_disable called <----")
		self.spi.xfer2([self.CMD_Write_Disable])
		if (self.check_wip_and_wel(expected_status=0x00, debug=debug) == 0):
			if (debug or self.debug):
				print("SUCCESSFUL write_disable")
			return 0
		else:
			print("ERROR, did not see WIP and WEL clear from write_disable")
			return -1

	# Bit   7   6   5   4   3   2   1   0
	#     SRP0 BP4 BP3 BP2 BP1 BP0 WEL WIP
	def read_status_register_1(self, debug=False):
		if (debug or self.debug):
			print("----> read_status_register_1 called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Status_Register_1, 0x00])
		return list_of_bytes[1]
		
	def check_wip_and_wel(self, num_attempts = 10, timestep = 0.001, expected_status = 0x00, debug=False):
		if (debug or self.debug):
			print("---->check_wip_and_wel called <----")
		attempts = 0
		while (attempts < 10):
			time.sleep(timestep)
			if ((self.read_status_register_1() & 0x03) == expected_status):
				break
			else:
				attempts += 1
		if (attempts == 10):
			print("ERROR WIP and WEL not at expected values after 10 attempts")
			return -1
		else:
			if (debug or self.debug):
				print("Number of attempts is {:d}".format(attempts))
			return 0
	
	def get_srp0_bit(self, degug=False):
		if (debug or self.debug):
			print("----> get_srp0_bit called <----")
		return (self.read_status_register_1() & 0x80) >> 7
	
	# Bit   7   6   5   4   3    2   1  0
	#     SUS1 CMP LB3 LB2 LB1 SUS2 QE SRP1
	def read_status_register_2(self, debug=False):
		if (debug or self.debug):
			print("----> read_status_register_2 called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Status_Register_2, 0x00])
		return list_of_bytes[1]
	
	# Bit   7    6    5   4     3        2        1        0
	# Reserved DRV1 DRV0 HPF Reserved Reserved Reserved Reserved 
	def read_status_register_3(self, debug=False):
		if (debug or self.debug):
			print("----> read_status_register_3 called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Status_Register_3, 0x00])
		return list_of_bytes[1]
	
	def get_srp1_bit(self, degug=False):
		if (debug or self.debug):
			print("----> get_srp1_bit called <----")
		return (self.read_status_register_2() & 0x01)
	
	# write_enable needed before status register can be written
	# Only one byte
	def write_status_register_1(self, write_bytes = [0x00], debug=False):
		if (debug or self.debug):
			print("----> write_status_register_1 called <----")
			print(write_bytes)
		self.write_enable()
		self.spi.xfer2([self.CMD_Write_Status_Register_1] + write_bytes)
	
	# write_enable needed before status register can be written
	# Only one byte
	def write_status_register_2(self, write_bytes = [0x00], debug=False):
		if (debug or self.debug):
			print("----> write_status_register_2 called <----")
			print(write_bytes)
		self.write_enable()
		self.spi.xfer2([self.CMD_Write_Status_Register_2] + write_bytes)
	
	def read_data(self, address=0x000000, num_bytes=1, debug=False):
		if (debug or self.debug):
			print("----> read_data called <----")
			print("Address is 0x{:06x}".format(address))
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Data, add_byte_upper, add_byte_mid, add_byte_lower] + [0x00]*num_bytes)
		if (debug or self.debug):
			print(list_of_bytes[4:])
		return list_of_bytes[4:]
	
	def continuous_read_mode_reset(self, debug=False):
		if (debug or self.debug):
			print("----> continuous_read_mode_reset called <----")
		self.spi.xfer2([self.CMD_Continuous_Read_Mode_Reset])

	# typical time is 0.6ms
	def program_page(self, address=0x000000, page_bytes=[], debug=False):
		if (debug or self.debug):
			print("----> program_page called <----")
			print("Address is 0x{:06x}".format(address))
			print(page_bytes)
		if (len(page_bytes) > 256):
			print("ERROR too many bytes for program_page given, {:d} bytes given".format(len(page_bytes)))
		if (self.write_enable() == 0):
			add_byte_upper = (address >> 16) & 0xFF
			add_byte_mid   = (address >> 8 ) & 0xFF
			add_byte_lower = (address      ) & 0xFF
			self.spi.xfer2([self.CMD_Page_Program, add_byte_upper, add_byte_mid, add_byte_lower] + page_bytes)
			if (self.check_wip_and_wel(timestep=0.0001, expected_status=0x00, debug=debug) == 0):
				if (debug or self.debug):
					print("SUCCESSFUL page program")
				return 0
			else:
				print("ERROR, did not see WIP and WEL clear after page_program")
				return -1

	# typical time is 45ms
	def sector_erase(self, address=0x000000, debug=False):
		if (debug or self.debug):
			print("----> sector_erase called <----")
			print("Address is 0x{:06x}".format(address))
		self.write_enable(debug=debug)
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		self.spi.xfer2([self.CMD_Sector_Erase, add_byte_upper, add_byte_mid, add_byte_lower])
		if (self.check_wip_and_wel(timestep=0.01, expected_status=0x00, debug=debug) == 0):
			if (debug or self.debug):
				print("SUCCESSFUL sector erase")
			return 0
		else:
			print("ERROR, did not see WIP and WEL clear after sector erase")
			return -1

	#typical time is 200ms
	def block_erase_32k(self, address=0x000000, debug=False):
		if (debug or self.debug):
			print("----> block_erase_32k called <----")
			print("Address is 0x{:06x}".format(address))
		self.write_enable(debug=debug)
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		self.spi.xfer2([self.CMD_Block_Erase_32K, add_byte_upper, add_byte_mid, add_byte_lower])
		if (self.check_wip_and_wel(timestep=0.1, expected_status=0x00, debug=debug) == 0):
			if (debug or self.debug):
				print("SUCCESSFUL block_erase_32k")
			return 0
		else:
			print("ERROR, did not see WIP and WEL clear after block_erase_32k")
			return -1
	
	#typical time is 200ms
	def block_erase_64k(self, address=0x000000, debug=False):
		if (debug or self.debug):
			print("----> block_erase_64k called <----")
			print("Address is 0x{:06x}".format(address))
		self.write_enable(debug=debug)
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		self.spi.xfer2([self.CMD_Block_Erase_64K, add_byte_upper, add_byte_mid, add_byte_lower])
		if (self.check_wip_and_wel(timestep=0.1, expected_status=0x00, debug=debug) == 0):
			if (debug or self.debug):
				print("SUCCESSFUL block_erase_64k")
			return 0
		else:
			print("ERROR, did not see WIP and WEL clear after block_erase_64k")
			return -1
	
	# typical time is 7s
	def chip_erase(self, debug=False):
		if (debug or self.debug):
			print("----> chip_erase called <----")
		self.write_enable(debug=debug)
		self.spi.xfer2([self.CMD_Chip_Erase])
		if (self.check_wip_and_wel(timestep=2.0, expected_status=0x00, debug=debug) == 0):
			if (debug or self.debug):
				print("SUCCESSFUL chip erase")
			return 0
		else:
			print("ERROR, did not see WIP and WEL clear after chip erase")
			return -1
	
	def enable_reset(self, debug=False):
		if (debug or self.debug):
			print("----> enable_reset called <----")
		self.spi.xfer2([self.CMD_Enable_Reset])
	
	def reset(self, debug=False):
		if (debug or self.debug):
			print("----> reset called <----")
		self.spi.xfer2([self.CMD_Reset])
		
	def program_erase_suspend(self, debug=False):
		if (debug or self.debug):
			print("----> program_rease_suspend called <----")
		self.spi.xfer2([self.CMD_Program_Erase_Suspend])
	
	def program_erase_resume(self, debug=False):
		if (debug or self.debug):
			print("----> program_rease_resume called <----")
		self.spi.xfer2([self.CMD_Program_Erase_Resume])

	def deep_power_down(self, debug=False):
		if (debug or self.debug):
			print("----> deep_power_down called <----")
		self.spi.xfer2([self.CMD_Deep_Power_Down])
	
	def release_from_deep_power_down(self, debug=False):
		if (debug or self.debug):
			print("----> release_from_deep_power_down called <----")
		self.spi.xfer2([self.CMD_Release_From_Deep_Power_Down])

	def release_from_deep_power_down_and_read_device_id(self, debug=False):
		if (debug or self.debug):
			print("----> release_from_deep_power_down_and_read_device_id called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Release_From_Deep_Power_Down] + [0x00]*4)
		if (debug or self.debug):
			print(list_of_bytes[4])
		return list_of_bytes[4]

	def manufacturer_device_id(self, debug=False):
		if (debug or self.debug):
			print("----> manufacturer_device_id called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Manufacturer_Device_ID] + [0x00]*5)
		if (list_of_bytes[3] != 0x00):
			print("ERROR expected byte #3 to be 0x00, but got 0x{:02x}".format(list_of_bytes[3]))
			return -1
		if (debug or self.debug):
			print(list_of_bytes[4:5])
		return list_of_bytes[4:]

	def read_unique_id(self, debug=False):
		if (debug or self.debug):
			print("----> read_unique_id called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Unique_ID] + [0x00]*12)
		if (debug or self.debug):
			print(list_of_bytes[5:])
		return list_of_bytes[5:]

	def read_identification(self, debug=False):
		if (debug or self.debug):
			print("----> read_identification called <----")
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Identification] + [0x00]*3)
		if (debug or self.debug):
			print(list_of_bytes[2:])
		return list_of_bytes[2:]

	def erase_security_registers(self, address=0x000000, debug=False):
		if (debug or self.debug):
			print("----> erase_security_registers called <----")
			print("Address is 0x{:06x}".format(address))
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		self.spi.xfer2([self.CMD_Erase_Security_Registers, add_byte_upper, add_byte_mid, add_byte_lower])

	def program_security_registers(self, address=0x000000, page_bytes=[], debug=False):
		if (debug or self.debug):
			print("----> program_security_registers called <----")
			print("Address is 0x{:06x}".format(address))
		if (address > 0x3FF):
			print("ERROR address given 0x{:06x} is too large, must be less than 0x0003FF".format(address))
			return -1
		if (len(page_bytes) > 256):
			print("ERROR too many bytes for program_page given, {:d} bytes given".format(len(page_bytes)))
			return -1
		if (len(page_bytes) == 0):
			print("Error must give at least 1 byte to program, none given")
			return -1
		add_byte_upper = (address >> 16) & 0xFF
		add_byte_mid   = (address >> 8 ) & 0xFF
		add_byte_lower = (address      ) & 0xFF
		self.spi.xfer2([self.CMD_Program_Security_Registers, add_byte_upper, add_byte_mid, add_byte_lower] + page_bytes)

	def read_security_register(self, address=0x000000, num_bytes=0, debug=False):
		if (debug or self.debug):
			print("----> read_security_registers called <----")
		if (address > 0x3FF):
			print("ERROR address given 0x{:06x} is too large, must be less than 0x0003FF".format(address))
			return -1
		if (len(page_bytes) > 256):
			print("ERROR too many bytes for program_page given, {:d} bytes given".format(len(page_bytes)))
			return -1
		if (num_bytes <  1):
			print("Error must set num_bytes to a value greater than zero")
			return -1
		if (address + num_bytes > 256):
			print("ERROR address of 0x{:06x} plus num_bytes of {:d} is greater than 256, out of range configuration".format(address,num_bytes))
			return -1
		list_of_bytes = self.spi.xfer2([self.CMD_Read_Security_Registers] + [0x00]*num_bytes)
		if (debug or self.debug):
			print(list_of_bytes[5:])
		return list_of_bytes[5:]
