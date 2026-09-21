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

def parse_properties(f, max_depth=10):
    props = {}
    while True:
        name = parse_str(f)
        if name == 'None' or not name:
            break
        type_data = f.read(4)
        if len(type_data) < 4:
            break
        length = struct.unpack('<i', type_data)[0]
        type_name = f.read(length)[:-1].decode('utf-8', errors='ignore') if length > 0 else ''
        
        size = struct.unpack('<Q', f.read(8))[0]
        
        if type_name == 'IntProperty':
            val = struct.unpack('<i', f.read(4))[0]
        elif type_name in ('StrProperty', 'NameProperty'):
            val = parse_str(f)
        elif type_name == 'FloatProperty':
            val = struct.unpack('<f', f.read(4))[0]
        elif type_name == 'ByteProperty':
            enum_name = parse_str(f)
            val = parse_str(f) if enum_name else struct.unpack('<B', f.read(1))[0]
        elif type_name == 'BoolProperty':
            val = struct.unpack('<B', f.read(1))[0] != 0
        elif type_name == 'QWordProperty':
            val = struct.unpack('<q', f.read(8))[0]
        elif type_name == 'StructProperty':
            struct_type = parse_str(f)
            start_pos = f.tell()
            val = parse_properties(f, max_depth - 1)
            read_bytes = f.tell() - start_pos
            if read_bytes < size:
                f.read(size - read_bytes)
        elif type_name == 'ArrayProperty':
            arr_len = struct.unpack('<i', f.read(4))[0]
            val = []
            for _ in range(arr_len):
                sub_props = parse_properties(f, max_depth - 1)
                val.append(sub_props)
        else:
            val = f.read(size)
            
        props[name] = val
    return props

def parse_replay_file(path):
    with open(path, 'rb') as f:
        header_size, crc, eng_v, lic_v = struct.unpack('<4i', f.read(16))
        if eng_v >= 868:
            net_v = struct.unpack('<i', f.read(4))[0]
        replay_class = parse_str(f)
        props = parse_properties(f)
        return props

for rf in os.listdir('raw_replays'):
    if rf.endswith('.replay'):
        path = os.path.join('raw_replays', rf)
        p = parse_replay_file(path)
        print(f"=== {rf} ===")
        print(f"Map: {p.get('MapName')}, Score: Blue {p.get('Team0Score')} - {p.get('Team1Score')} Orange, Frames: {p.get('NumFrames')}")
        goals = p.get('Goals', [])
        print(f"Goals count: {len(goals)}")
        for g in goals:
            print(f"  Goal at frame {g.get('frame')}: {g.get('PlayerName')} (Team {g.get('PlayerTeam')})")
        players = p.get('PlayerStats', [])
        print(f"PlayerStats count: {len(players)}")
        for ps in players:
            print(f"  Player: {ps.get('Name')} | Team: {ps.get('Team')} | Score: {ps.get('Score')} | Goals: {ps.get('Goals')} | Saves: {ps.get('Saves')} | Shots: {ps.get('Shots')} | Assists: {ps.get('Assists')}")
