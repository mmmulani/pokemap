#!/usr/bin/env python3.3

import struct
import sys
from optparse import OptionParser

DEBUG_MODE = False
def debug(*args, **kwargs):
  if DEBUG_MODE:
    print(*args, **kwargs)

def main():
  parser = OptionParser(usage="usage: %prog pokemon-rom")
  parser.add_option("-v", "--verbose",
    help="Print information while running to help debug", action="store_true",
    dest="verbose")
  (options, args) = parser.parse_args()

  global DEBUG_MODE
  if options.verbose:
    DEBUG_MODE = True

  analyse_rom(args[0], '0x3526A8')

def analyse_rom(rom_path, hex_offset):
  bytes = open(rom_path, 'rb').read()
  offset = int(hex_offset, 16)

  bank_pointers = []
  while is_pointer(bytes, offset):
    bank_pointer = read_pointer(bytes, offset)
    bank_pointers.append(bank_pointer)
    offset = offset + 4

  debug('Found these bank pointers: {}'.format(bank_pointers))

  banks = []
  for i, bank_pointer in enumerate(bank_pointers):
    offset = bank_pointer
    next_pointer = bank_pointers[i + 1] if (i + 1) < len(bank_pointers) else 0

    maps = []
    while is_pointer(bytes, offset):
      map_pointer = read_pointer(bytes, offset)
      maps.append(map_pointer)

      offset = offset + 4
      if offset == next_pointer:
        break

    debug('Found {} map pointers: {}'.format(len(maps), maps))
    banks.append(maps)

  # Pallet Town
  pallet_town = banks[3][0]
  read_map(bytes, pallet_town)

def read_map(bytes, header_pointer):
  map_pointer = read_pointer(bytes, header_pointer)
  width = read_int(bytes, map_pointer)
  height = read_int(bytes, map_pointer + 4)
  border = read_pointer(bytes, map_pointer + 8)
  tiles = read_pointer(bytes, map_pointer + 12)

  debug('Map at {}'.format(map_pointer))
  debug('Width/height: {}/{}'.format(width, height))
  debug('Border pointer: {0:#x}, tiles pointer: {1:#x}'.format(border, tiles))

  tile_sprites = {}

  i = 0
  for y in range(height):
    for x in range(width):
      tile_data = \
        struct.unpack('<H', bytes[(tiles + i * 2):(tiles + (i + 1) * 2)])[0]
      attribute = tile_data >> 10
      tile = tile_data & 0x3ff
      debug('tile at ({}, {}): {:#x}, attribute: {:#x}'.format(
        x, y, tile, attribute))


      i = i + 1
  return tile_data

def is_pointer(bytes, offset):
  return read_pointer(bytes, offset) > 0

def read_pointer(bytes, offset):
  load_address = int('0x8000000', 16)
  return read_int(bytes, offset) - load_address

def read_int(bytes, offset):
  return struct.unpack(b'<I', bytes[offset:(offset + 4)])[0]

if __name__ == '__main__':
  main()