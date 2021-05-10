from __future__ import print_function
from gd25q32c   import gd25q32c

spi_flash = gd25q32c(max_speed_hz=6000000) # 6MHz
print("Status Register 1 is 0x{:02x}".format(spi_flash.read_status_register_1()))
print("Status Register 2 is 0x{:02x}".format(spi_flash.read_status_register_2()))
print("Status Register 3 is 0x{:02x}".format(spi_flash.read_status_register_3()))
print("Unique ID bytes are as follows:")
print([hex(x) for x in spi_flash.read_unique_id()])
print("Identification bytes are as follows:")
print([hex(x) for x in spi_flash.read_identification()])
#print("Manufacturer Device ID bytes are as follows:")
#print(spi_flash.manufacturer_device_id())
print("Erase entire device")
spi_flash.chip_erase(debug=True)
print("Read first and last pages")
print(spi_flash.read_data(address=(0 * spi_flash.PAGE_size_addr), num_bytes=256)) # first page
print(spi_flash.read_data(address=((spi_flash.NUM_PAGES - 1) * spi_flash.PAGE_size_addr), num_bytes=256)) # last page
print("Program all pages to have sequential values (this should take 16384 * 0.6ms = 10 seconds, but takes 18 seconds due to SPI frequency")
list_page_of_bytes = list(range(0, 256))
for pages in range(0,spi_flash.NUM_PAGES):
	spi_flash.program_page(address=(pages * spi_flash.PAGE_size_addr), page_bytes=list_page_of_bytes, debug=False)
print("Read first and last pages")
print(spi_flash.read_data(address=(0 * spi_flash.PAGE_size_addr), num_bytes=256)) # first page
print(spi_flash.read_data(address=((spi_flash.NUM_PAGES - 1) * spi_flash.PAGE_size_addr), num_bytes=256)) # last page
print("Erase first sector")
spi_flash.sector_erase(address=(0 * spi_flash.SECTOR_size_addr), debug=True) # sector 0
print("Read first and last pages")
print(spi_flash.read_data(address=(0 * spi_flash.PAGE_size_addr), num_bytes=256)) # first page
print(spi_flash.read_data(address=((spi_flash.NUM_PAGES - 1) * spi_flash.PAGE_size_addr), num_bytes=256)) # last page
print("Erase last 64k block")
spi_flash.block_erase_64k(address=((spi_flash.NUM_BLOCKS_size_64k - 1) * spi_flash.BLOCK_size_64k_addr)) # last 64k block
print("Read first and last pages")
print(spi_flash.read_data(address=(0 * spi_flash.PAGE_size_addr), num_bytes=256)) # first page
print(spi_flash.read_data(address=((spi_flash.NUM_PAGES - 1) * spi_flash.PAGE_size_addr), num_bytes=256)) # last page
