#!/usr/bin/python

from __future__ import print_function
import argparse
import json

class SDKDBComparator:
    @staticmethod
    def diff(base, value, context=''):
        diff_type = type(value).__name__
        diff_method = getattr(
            SDKDBComparator, f"diff_{diff_type}", SDKDBComparator.diff_builtin
        )
        return diff_method(base, value, context)

    @staticmethod
    def diff_builtin(base, value, context=''):
        if base != value:
            print(f'SDKDB{context} is not equal: {base} vs {value}', end=' ')
            return False
        return True

    @staticmethod
    def diff_dict(base, value, context=''):
        for key, entry in base.iteritems():
            if key not in value.keys():
                print(f'key {key} missing from dict {context}', end=' ')
                return False
            if not SDKDBComparator.diff(entry, value[key], f'{context}[{key}]'):
                return False
        return True

    @staticmethod
    def diff_list(base, value, context=''):
        for index, (base_value, new_value) in enumerate(zip(base, value)):
            context_name = index
            if isinstance(new_value, dict):
                try:
                    context_name = new_value['name']
                except KeyError:
                    pass
            if not SDKDBComparator.diff(
                base_value, new_value, f'{context}[{context_name}]'
            ):
                return False
        return True


def compare_sdkdb_entry(baseline, value):
    name = value['binaryInfo']['installName']
    equal = True

    equal &= SDKDBComparator.diff(baseline, value)

    if not equal:
        print(f'in library {name}')

    return equal


def compare_target_list(baseline, new_list):
    # build a lookup map
    lookup_map = {}
    for item in new_list:
        name = item['binaryInfo']['installName']
        if len(name) != 0:
            lookup_map[name] = item

    for item in baseline:
        name = item['binaryInfo']['installName']
        if len(name) != 0:
            try:
                compare_target = lookup_map[name]
            except KeyError:
                print(f'Missing {name} from SDKDB')
                return False
            else:
                compare_sdkdb_entry(item, compare_target)
    return True


def is_sdkdb_public(sdkdb):
    return sdkdb.get('public', False)


def compare_sdkdb(baseline, sdkdb):
    """compare two sdkdb objects"""
    for key, value in baseline.iteritems():
        if key == 'public':
            if is_sdkdb_public(sdkdb):
                continue

            print('Comparing public to private is not supported')
            return False
        if key not in sdkdb.keys():
            print(f'Target {key} missing from SDKDB')
            return False

        if not compare_target_list(value, sdkdb[key]):
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description='Diff SDKDB.')

    parser.add_argument('base', help='baseline SDKDB')
    parser.add_argument('sdkdb', help='new SDKDB to compare')

    args = parser.parse_args()

    with open(args.base, 'r') as f:
        baseline = json.load(f)
    with open(args.sdkdb, 'r') as f:
        sdkdb = json.load(f)

    compare_sdkdb(baseline, sdkdb)


if __name__ == '__main__':
    main()
