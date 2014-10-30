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
  strings = load_strings(bytes, '0x3eecfc')
  debug('Found all these strings: {}'.format(strings))
  banks = find_banks(bytes, '0x3526A8')

  pygame.init()

  for map_ in banks[3]:
    draw_and_save_map(bytes, map_, strings)
    pygame.time.wait(1000)

  pygame.quit()

def load_rom(rom_path):
  return open(rom_path, 'rb').read()

def load_strings(bytes, hex_offset):
  offset = int(hex_offset, 16)
  table = {
    0x00:' ',0x01:'À',0x02:'Á',0x03:'Â',0x04:'Ç',0x05:'È',0x06:'É',0x07:'Ê',
    0x08:'Ë',0x09:'Ì',0x0B:'Î',0x0C:'Ï',0x0D:'Ò',0x0E:'Ó',0x0F:'Ô',0x10:'Œ',
    0x11:'Ù',0x12:'Ú',0x13:'Û',0x14:'Ñ',0x15:'ß',0x16:'à',0x17:'á',0x19:'ç',
    0x1A:'è',0x1B:'é',0x1C:'ê',0x1D:'ë',0x1E:'ì',0x20:'î',0x21:'ï',0x22:'ò',
    0x23:'ó',0x24:'ô',0x25:'œ',0x26:'ù',0x27:'ú',0x28:'û',0x29:'ñ',0x2A:'º',
    0x2B:'ª',0x2D:'&',0x2E:'+',0x34:'[Lv]',0x35:'=',0x36:';',0x51:'¿',0x52:'¡',
    0x53:'[pk]',0x54:'[mn]',0x55:'[po]',0x56:'[ké]',0x57:'[bl]',0x58:'[oc]',
    0x59:'[k]',0x5A:'Í',0x5B:'%',0x5C:'(',0x5D:')',0x68:'â',0x6F:'í',0x79:'[U]',
    0x7A:'[D]',0x7B:'[L]',0x7C:'[R]',0x85:'<',0x86:'>',0xA1:'0',0xA2:'1',
    0xA3:'2',0xA4:'3',0xA5:'4',0xA6:'5',0xA7:'6',0xA8:'7',0xA9:'8',0xAA:'9',
    0xAB:'!',0xAC:'?',0xAD:'.',0xAE:'-',0xAF:'·',0xB0:'...',0xB1:'«',0xB2:'»',
    0xB3:'\'',0xB4:'\'',0xB5:'|m|',0xB6:'|f|',0xB7:'$',0xB8:',',0xB9:'*',
    0xBA:'/',0xBB:'A',0xBC:'B',0xBD:'C',0xBE:'D',0xBF:'E',0xC0:'F',0xC1:'G',
    0xC2:'H',0xC3:'I',0xC4:'J',0xC5:'K',0xC6:'L',0xC7:'M',0xC8:'N',0xC9:'O',
    0xCA:'P',0xCB:'Q',0xCC:'R',0xCD:'S',0xCE:'T',0xCF:'U',0xD0:'V',0xD1:'W',
    0xD2:'X',0xD3:'Y',0xD4:'Z',0xD5:'a',0xD6:'b',0xD7:'c',0xD8:'d',0xD9:'e',
    0xDA:'f',0xDB:'g',0xDC:'h',0xDD:'i',0xDE:'j',0xDF:'k',0xE0:'l',0xE1:'m',
    0xE2:'n',0xE3:'o',0xE4:'p',0xE5:'q',0xE6:'r',0xE7:'s',0xE8:'t',0xE9:'u',
    0xEA:'v',0xEB:'w',0xEC:'x',0xED:'y',0xEE:'z',0xEF:'|>|',0xF0:':',0xF1:'Ä',
    0xF2:'Ö',0xF3:'Ü',0xF4:'ä',0xF5:'ö',0xF6:'ü',0xF7:'|A|',0xF8:'|V|',
    0xF9:'|<|',0xFA:'|nb|',0xFB:'|nb2|',0xFC:'|FC|',0xFD:'|FD|',0xFE:'|br|',
  }
  strings = []
  string = ''
  while True:
    char = struct.unpack('<B', bytes[offset:(offset + 1)])[0]
    offset = offset + 1
    if char == 0xff:
      strings.append(string)
      string = ''
      continue
    elif char not in table:
      break
    string += table[char]
  return strings

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
  label = struct.unpack('<B', bytes[(header_pointer + 20):(header_pointer + 21)])[0]
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

  return (width, height, label, tile_sprites, tileset_pointer, local_pointer)

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

def draw_and_save_map(bytes, map_, strings):
  (width, height, label, tile_sprites, global_pointer, local_pointer) = read_map(bytes, map_)
  (palettes, tiles, blocks) = read_tileset(bytes, global_pointer)
  (extra_palettes, extra_tiles, extra_blocks) = read_tileset(bytes, local_pointer)
  palettes.extend(extra_palettes)
  tiles.extend(extra_tiles)
  blocks.extend(extra_blocks)

  screen = pygame.display.set_mode((width * 16, height * 16))
  screen.fill((255, 255, 255))

  for (x, y) in tile_sprites:
    draw_block(screen, palettes, tiles, blocks, x * 16, y * 16, tile_sprites[(x, y)])

  pygame.display.flip()

  name = strings[label - 88]
  pygame.image.save(screen, 'maps/{}.bmp'.format(name))

def is_pointer(bytes, offset):
  return read_pointer(bytes, offset) > 0

def read_pointer(bytes, offset):
  load_address = int('0x8000000', 16)
  return read_int(bytes, offset) - load_address

def read_int(bytes, offset):
  return struct.unpack(b'<I', bytes[offset:(offset + 4)])[0]

if __name__ == '__main__':
  main()