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

def parse_property_dict(f):
    props = {}
    while True:
        name = parse_str(f)
        if name == 'None' or not name:
            break
        ptype_len_data = f.read(4)
        if len(ptype_len_data) < 4: break
        ptype_len = struct.unpack('<i', ptype_len_data)[0]
        ptype = f.read(ptype_len)[:-1].decode('utf-8', errors='ignore') if ptype_len > 0 else ''
        psize = struct.unpack('<Q', f.read(8))[0]
        
        if ptype == 'IntProperty':
            val = struct.unpack('<i', f.read(4))[0]
        elif ptype in ('StrProperty', 'NameProperty'):
            val = parse_str(f)
        elif ptype == 'FloatProperty':
            val = struct.unpack('<f', f.read(4))[0]
        elif ptype == 'ByteProperty':
            enum_name = parse_str(f)
            val = parse_str(f) if enum_name else struct.unpack('<B', f.read(1))[0]
        elif ptype == 'BoolProperty':
            val = struct.unpack('<B', f.read(1))[0] != 0
        elif ptype == 'QWordProperty':
            val = struct.unpack('<q', f.read(8))[0]
        elif ptype == 'StructProperty':
            struct_type = parse_str(f)
            val = f.read(psize)
        elif ptype == 'ArrayProperty':
            arr_len = struct.unpack('<i', f.read(4))[0]
            val = []
            for _ in range(arr_len):
                val.append(parse_property_dict(f))
        else:
            val = f.read(psize)
        props[name] = val
    return props

def full_parse(path):
    with open(path, 'rb') as f:
        header_size, crc, eng_v, lic_v = struct.unpack('<4i', f.read(16))
        if eng_v >= 868:
            net_v = struct.unpack('<i', f.read(4))[0]
        replay_class = parse_str(f)
        props = parse_property_dict(f)
        return props

for rf in os.listdir('raw_replays'):
    if rf.endswith('.replay'):
        path = os.path.join('raw_replays', rf)
        p = full_parse(path)
        print(f"=== {rf} ===")
        print(f"MapName: {p.get('MapName')}, Team0Score: {p.get('Team0Score')}, Team1Score: {p.get('Team1Score')}, NumFrames: {p.get('NumFrames')}, RecordFPS: {p.get('RecordFPS')}")
        print(f"Goals: {p.get('Goals')}")
        print("Players:")
        for ps in p.get('PlayerStats', []):
            print(f"  {ps.get('Name')} -> Team: {ps.get('Team')}, Score: {ps.get('Score')}, G:{ps.get('Goals')}, A:{ps.get('Assists')}, S:{ps.get('Saves')}, Sh:{ps.get('Shots')}")
