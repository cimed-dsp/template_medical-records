'''This module creates dictionaries mapping ICD to CCS, and also
CCS codes to their text descriptions.  You can get the code files here:
https://www.hcup-us.ahrq.gov/toolssoftware/ccs/ccs.jsp

We use the single level csv files for this.  The outputs of these files are
used later in process_mimic.py for creating the label files used to train
the model.

inputs:
    - Single Level file from CCS.
outputs:
    - Dictionary of ICD to CCS codes as JSON file.
    - Dictionary of CCS codes to their descriptions as JSON file.

'''

import argparse
import json
import os

def get_code_mapping(in_file, out_dir, n_header_rows):

    ccs_map = {}
    ccs_translation = {}
    with open(in_file, 'r') as ref:
        # throw away headers
        for header in range(n_header_rows):
            throw = ref.readline()

        # for each ccs code, create list of icd9 codes that map to it
        for line in ref:
            fields = line.replace("'", "").split(',')  # csv split row
            [icd, ccs, ccs_description, icd_description] = fields[:4]
            if int(ccs) in ccs_map.keys():
                ccs_map[int(ccs)].append(icd.strip())
            else:
                ccs_map[int(ccs)] = [icd.strip()]
                ccs_translation[int(ccs)] = str(ccs_description)
        ccs_codes = list(ccs_map.keys())

    # output as dict to be read in and used to 'translate' diagnosis codes in doctorai
    basename = os.path.splitext(os.path.basename(in_file))[0]
    ccs_map_path = os.path.join(out_dir, basename + '.json')
    with open(ccs_map_path, 'w', encoding='utf8') as ccs_map_file:
        json.dump(ccs_map, ccs_map_file, indent=2)
    ccs_translation_path = os.path.join(out_dir, basename + '_text.json')
    with open(ccs_translation_path, 'w', encoding='utf8') as ccs_translation_file:
        json.dump(ccs_translation, ccs_translation_file, indent=2)

def parse_arguments(parser):
    parser.add_argument(\
        'in_file',
        type=str,
        help='The path to the single-level CCS csv file.')
    parser.add_argument(\
        'out_dir',
        type=str,
        help='The output directory.')
    parser.add_argument(\
        'n_header_rows',
        type=int,
        help='The number of header rows found in the single-level CCS csv file.')
    args = parser.parse_args()
    return args

def main():
    parser = argparse.ArgumentParser()
    args = parse_arguments(parser)
    get_code_mapping(args.in_file, args.out_dir, args.n_header_rows)

if __name__ == '__main__':
    main()
