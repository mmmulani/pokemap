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

  offset = read_pointer(bytes, tileset_pointer + 8)
  palettes = []
  for i in range(16):
    palette = []
    for j in range(16):
      colours = \
      struct.unpack('<H',
        bytes[(offset + (i * 32) + (j * 2)):\
          (offset + (i * 32) + ((j + 1) * 2))])[0]
      (r, g, b) = (colours & 0x1f, (colours >> 5) & 0x1f, colours >> 10)
      (r, g, b) = (r * 8, g * 8, b * 8)
      palette.append((r, g, b))
    palettes.append(palette)

  offset = read_pointer(bytes, tileset_pointer + 12)
  blocks = []
  for i in range(0x2d8):
    down = []
    for j in range(4):
      block_data = \
        struct.unpack('<H', bytes[(offset + i * 16 + j * 2):(offset + i * 16 + (j + 1) * 2)])[0]
      palette = block_data >> 12
      tile = block_data & 0x3ff
      attributes = (block_data >> 10) & 0x3
      down.append((palette, tile, attributes))

    up = []
    for j in range(4, 8):
      block_data = \
        struct.unpack('<H', bytes[(offset + i * 16 + j * 2):(offset + i * 16 + (j + 1) * 2)])[0]
      palette = block_data >> 12
      tile = block_data & 0x3ff
      attributes = (block_data >> 10) & 0x3
      up.append((palette, tile, attributes))

    blocks.append((down, up))

  pygame.init()
  screen = pygame.display.set_mode((300, 1000))
  screen.fill((255, 255, 255))

  for i in range(0x2d8):
    x = i % 8
    y = int(i / 8)
    draw_block(screen, palettes, tiles, blocks, x * 16, y * 16, i)

  pygame.display.flip()

  while True:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        pygame.quit()

def draw_block(screen, palettes, tiles, blocks, x, y, block_num):
  (down, up) = blocks[block_num]
  for i, (palette, tile, attributes) in enumerate(down):
    x_offset = (i % 2) * 8
    y_offset = int(i / 2) * 8
    draw_tile(screen, palettes[palette], tiles[tile],
      x + x_offset, y + y_offset, attributes, False)

  for i, (palette, tile, attributes) in enumerate(up):
    x_offset = (i % 2) * 8
    y_offset = int(i / 2) * 8
    draw_tile(screen, palettes[palette], tiles[tile],
      x + x_offset, y + y_offset, attributes, True)

def draw_tile(screen, palette, tile, x, y, attributes, mask_mode):
  x_flip = attributes & 0x1
  y_flip = attributes & 0x2
  for i, px in enumerate(tile):
    x_offset = (i % 8)
    if x_flip:
      x_offset = 8 - (x_offset + 1)

    y_offset = int(i / 8)
    if y_flip:
      y_offset = 8 - (y_offset + 1)

    if mask_mode and px == 0:
      continue
    colour = palette[px]
    screen.set_at((x + x_offset, y + y_offset), colour)

def is_pointer(bytes, offset):
  return read_pointer(bytes, offset) > 0

def read_pointer(bytes, offset):
  load_address = int('0x8000000', 16)
  return read_int(bytes, offset) - load_address

def read_int(bytes, offset):
  return struct.unpack(b'<I', bytes[offset:(offset + 4)])[0]

if __name__ == '__main__':
  main()