"""Read-only Amos serialized-text model structure audit (no estimation)."""
import collections
import json
from pathlib import Path


def parse(path):
    lines = path.read_text(encoding='utf-16').splitlines()
    ia = lines.index('!@!at')
    width = int(lines[ia+1])
    fields = [line.split(',')[0] for line in lines[ia+2:ia+2+width]]
    io = lines.index('!@!ob')
    count = int(lines[io+1])
    objects = []
    for index in range(count):
        start = io+2+index*width
        record = dict(zip(fields, lines[start:start+width]))
        record['id'] = index+1
        objects.append(record)
    assert lines[io+2+count*width] == '!@!ee'
    settings_start = lines.index('!@!dollar') + 1
    settings_end = lines.index('EndDollar', settings_start)
    settings = lines[settings_start:settings_end]
    nodes = [{'id': obj['id'], 'type': int(obj['o_type']), 'name': obj['label'],
              'longlabel': obj['longlabel'], 'value1_raw': obj['value1'],
              'value2_raw': obj['value2']} for obj in objects
             if int(obj['o_type']) in (1, 2)]
    by_id = {obj['id']:obj for obj in objects}
    arrows = []
    for obj in objects:
        if int(obj['obj1']) != 0 or int(obj['obj2']) != 0:
            one, two = int(obj['obj1']), int(obj['obj2'])
            arrows.append({'id': obj['id'], 'type': int(obj['o_type']),
                           'obj1_id': one, 'obj2_id': two,
                           'obj1_name': by_id[one]['label'] if one else None,
                           'obj2_name': by_id[two]['label'] if two else None,
                           'value1_raw': obj['value1'], 'value2_raw': obj['value2']})
    return {'source': path.name, 'source_modified':False, 'estimated':False,
            'attribute_count': width, 'object_count': count,
            'object_types': dict(collections.Counter(int(obj['o_type']) for obj in objects)),
            'settings':settings, 'nodes':nodes, 'arrows':arrows}


if __name__ == '__main__':
    work = Path(__file__).resolve().parent
    result = parse(work.parent / 'amos模型.amw')
    (work/'amw_structure_audit.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
