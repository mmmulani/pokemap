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
  (tile_sprites, global_pointer, local_pointer) = read_map(bytes, pallet_town)
  (palettes, tiles, blocks) = read_tileset(bytes, global_pointer)
  (extra_palettes, extra_tiles, extra_blocks) = read_tileset(bytes, local_pointer)
  palettes.extend(extra_palettes)
  tiles.extend(extra_tiles)
  blocks.extend(extra_blocks)

  pygame.init()
  screen = pygame.display.set_mode((300, 1000))
  screen.fill((255, 255, 255))

  for (x, y) in tile_sprites:
    draw_block(screen, palettes, tiles, blocks, x * 16, y * 16, tile_sprites[(x, y)])

  pygame.display.flip()

  while True:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        pygame.quit()


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
  local_pointer = read_pointer(bytes, map_pointer + 20)

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

  return (tile_sprites, tileset_pointer, local_pointer)

def read_tileset(bytes, tileset_pointer):
  attribs = struct.unpack('<2B', bytes[tileset_pointer:(tileset_pointer + 2)])
  debug('Tileset compressed: {}, primary: {}'.format(attribs[0], attribs[1]))
  primary = attribs[1]
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
  debug('Total number of tiles read: {}'.format(len(tiles)))

  offset = read_pointer(bytes, tileset_pointer + 8)
  debug('Palette pointer: {:#x}'.format(offset))
  palette_range = range(7) if primary == 0 else range(7, 16)
  palettes = []
  for i in palette_range:
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
  end = read_pointer(bytes, tileset_pointer + 20)
  total_blocks = (end - offset) / 16
  debug('trying to read {} blocks'.format(total_blocks))
  blocks = []
  for i in range(int(total_blocks)):
    blocks.append(read_block(bytes, offset, i))

  return (palettes, tiles, blocks)

def read_second_blocks(bytes, header_pointer):
  map_pointer = read_pointer(bytes, header_pointer)
  tileset_pointer = read_pointer(bytes, map_pointer + 20)
  offset = read_pointer(bytes, tileset_pointer + 12)
  blocks = []
  for i in range(96):
    b = read_block(bytes, offset, i)
    blocks.append(b)
  return blocks

def read_block(bytes, offset, i):
  block = []
  for j in range(8):
    block_data = \
      struct.unpack('<H', bytes[(offset + i * 16 + j * 2):(offset + i * 16 + (j + 1) * 2)])[0]
    palette = block_data >> 12
    tile = block_data & 0x3ff
    attributes = (block_data >> 10) & 0x3
    block.append((palette, tile, attributes))
  return block

def draw_block(screen, palettes, tiles, blocks, x, y, block_num):
  # The first four tiles are the bottom tiles and the last four are the top
  # ones. The top tiles also have a mask to them, so we have to draw them
  # differently.
  block = blocks[block_num]
  for i, (palette, tile, attributes) in enumerate(block):
    x_offset = (i % 2) * 8
    y_offset = int((i % 4) / 2) * 8
    draw_tile(screen, palettes[palette], tiles[tile],
      x + x_offset, y + y_offset, attributes, i >= 4)

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