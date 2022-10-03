import argparse

# Setting cli arguments
parser = argparse.ArgumentParser(description='Get groups.')
parser.add_argument('-s', '--struct', dest='structureId', type=int, nargs='?', help='Structure ID')
parser.add_argument('faculty-id', type=str, help='Faculty ID')
parser.add_argument('course', type=str, help='Course')

def parse_cmd_args():
    'Get command line arguments'

    args = parser.parse_args()
    return vars(args)
