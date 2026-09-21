import struct
import os

def parse_str(f):
    data = f.read(4)
    if len(data) < 4: return ''
    length = struct.unpack('<i', data)[0]
    if length == 0: return ''
    if length < 0:
        raw = f.read(-length * 2)
        return raw[:-2].decode('utf-16', errors='ignore')
    raw = f.read(length)
    return raw[:-1].decode('utf-8', errors='ignore')

def inspect_player_stats(path):
    with open(path, 'rb') as f:
        header_size, crc, eng_v, lic_v = struct.unpack('<4i', f.read(16))
        if eng_v >= 868:
            net_v = struct.unpack('<i', f.read(4))[0]
        replay_class = parse_str(f)
        print("Replay Class:", replay_class)
        
        while True:
            name = parse_str(f)
            if name == 'None' or not name:
                print("End of root props")
                break
            type_data = f.read(4)
            if len(type_data) < 4: break
            length = struct.unpack('<i', type_data)[0]
            type_name = f.read(length)[:-1].decode('utf-8', errors='ignore') if length > 0 else ''
            size = struct.unpack('<Q', f.read(8))[0]
            print(f"Prop: {name} ({type_name}, size={size})")
            
            if name == 'PlayerStats':
                arr_len = struct.unpack('<i', f.read(4))[0]
                print(f"  PlayerStats array length: {arr_len}")
                for p_idx in range(arr_len):
                    print(f"  --- Player {p_idx} ---")
                    while True:
                        pname = parse_str(f)
                        if pname == 'None' or not pname:
                            print("    None (end of player)")
                            break
                        ptype_len = struct.unpack('<i', f.read(4))[0]
                        ptype = f.read(ptype_len)[:-1].decode('utf-8', errors='ignore') if ptype_len > 0 else ''
                        psize = struct.unpack('<Q', f.read(8))[0]
                        print(f"    {pname} : {ptype} (size={psize})")
                        if ptype == 'IntProperty':
                            val = struct.unpack('<i', f.read(4))[0]
                            print(f"      val = {val}")
                        elif ptype in ('StrProperty', 'NameProperty'):
                            val = parse_str(f)
                            print(f"      val = {val}")
                        elif ptype == 'ByteProperty':
                            enum_name = parse_str(f)
                            val = parse_str(f) if enum_name else struct.unpack('<B', f.read(1))[0]
                            print(f"      val = {val} (enum: {enum_name})")
                        elif ptype == 'BoolProperty':
                            val = struct.unpack('<B', f.read(1))[0] != 0
                            print(f"      val = {val}")
                        elif ptype == 'QWordProperty':
                            val = struct.unpack('<q', f.read(8))[0]
                            print(f"      val = {val}")
                        elif ptype == 'StructProperty':
                            struct_type = parse_str(f)
                            print(f"      StructType = {struct_type}")
                            struct_data = f.read(psize)
                            print(f"      Struct raw data len = {len(struct_data)}")
                        else:
                            val = f.read(psize)
                break
            else:
                # skip property
                f.read(size)

inspect_player_stats('raw_replays/3ab6f33e-11e4-42c8-bfce-f8c9485ece35.replay')
