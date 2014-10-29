#!/usr/bin/env python3.3

import nlzss.lzss3
import pygame
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

  bytes = load_rom(args[0])
  banks = find_banks(bytes, '0x3526A8')

  pallet_town = banks[3][0]
  (tile_splites, header_pointer) = read_map(bytes, pallet_town)
  draw_tileset(bytes, header_pointer)

def load_rom(rom_path):
  return open(rom_path, 'rb').read()

def find_banks(bytes, hex_offset):
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

  return banks

def read_map(bytes, header_pointer):
  map_pointer = read_pointer(bytes, header_pointer)
  width = read_int(bytes, map_pointer)
  height = read_int(bytes, map_pointer + 4)
  border = read_pointer(bytes, map_pointer + 8)
  tiles_pointer = read_pointer(bytes, map_pointer + 12)
  tileset_pointer = read_pointer(bytes, map_pointer + 16)

  debug('Map at {}'.format(map_pointer))
  debug('Width/height: {}/{}'.format(width, height))
  debug('Border pointer: {0:#x}, tiles pointer: {1:#x}'.format(
    border, tiles_pointer))

  tile_sprites = {}

  offset = tiles_pointer
  i = 0
  for y in range(height):
    for x in range(width):
      tile_data = \
        struct.unpack('<H', bytes[(offset + i * 2):(offset + (i + 1) * 2)])[0]
      attribute = tile_data >> 10
      tile = tile_data & 0x3ff
      debug('tile at ({}, {}): {:#x}, attribute: {:#x}'.format(
        x, y, tile, attribute))
      tile_sprites[(x, y)] = tile

      i = i + 1

  return (tile_sprites, tileset_pointer)

def draw_tileset(bytes, tileset_pointer):
  tileset_image_pointer = read_pointer(bytes, tileset_pointer + 4)
  image = nlzss.lzss3.decompress_bytes(bytes[tileset_image_pointer:])

  pygame.init()
  screen = pygame.display.set_mode((300, 1000))
  screen.fill((255, 255, 255))
  palette = [
    (0, 0, 0),
    (184, 248, 136),
    (128, 208, 96),
    (56, 144, 48),
    (56, 88, 16),
    (112, 96, 96),
    (64, 56, 48),
    (248, 0, 248),
    (136, 216, 184),
    (248, 192, 112),
    (232, 128, 104),
    (192, 48, 64),
    (160, 224, 192),
    (112, 200, 160),
    (64, 176, 136),
    (24, 160, 104),
  ]
  tiles = []
  for i in range(0, len(image), 32):
    tile = []
    for j in range(64):
      px = image[int(i + (j / 2))]
      if j % 2 == 0:
        px = px & 0xf
      else:
        px = int(px / 0x10)
      tile.append(px)
    tiles.append(tile)

  w = 2
  for i, tile in enumerate(tiles):
    x = (i % 16) * 16
    y = int(i / 16) * 16
    for j, px in enumerate(tile):
      xx = j % 8
      yy = int(j / 8)
      colour = palette[px]
      pygame.draw.rect(screen, colour,
        (x + xx * w, y + yy * w, w, w))

  debug('image length: {}'.format(len(image)))
  pygame.display.flip()

  while True:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        pygame.quit()

def is_pointer(bytes, offset):
  return read_pointer(bytes, offset) > 0

def read_pointer(bytes, offset):
  load_address = int('0x8000000', 16)
  return read_int(bytes, offset) - load_address

def read_int(bytes, offset):
  return struct.unpack(b'<I', bytes[offset:(offset + 4)])[0]

if __name__ == '__main__':
  main()