'''This script processes MIMIC-III dataset and builds longitudinal diagnosis records
for patients with at least two visits.
The output data are cPickled, and suitable for training Doctor AI or RETAIN
Written by Edward Choi (mp2893@gatech.edu)
Usage: Put this script to the folder where MIMIC-III CSV files are located. Then execute the
below command.
python process_mimic.py ADMISSIONS.csv DIAGNOSES_ICD.csv <output file>

-inputs:
    -ADMISSIONS.csv file from MIMIC
    -DIAGNOSES_ICD.csv file from MIMIC
    -output file name.

-outputs
    -<output file>.pids: List of unique Patient IDs. Used for intermediate processing
    -<output file>.dates: List of List of Python datetime objects. The outer List is for each
                          patient. The inner List is for each visit made by each patient
    -<output file>.seqs: List of List of List of integer diagnosis codes. The outer List is for
                         each patient. The middle List contains visits made by each patient.
                         The inner List contains the integer diagnosis codes that occurred in
                         each visit
    -<output file>.types: Python dictionary that maps string diagnosis codes to
                          integer diagnosis codes.

# Edited 2/6/2020 Eliot Bethke
# -updated print syntax to python3 compat
# -updated 'iteritems' syntax to 'items' to python3 compat
# -added train, valid, test splitting by 60/20/20 fixed percentages
# -imports ccs code dictionary with 'CCS code' (key) : [ICD9 codes...] (value)
# Edited 7/10/2020 Matt Berry
# -delinted
# -switched to argparse
# -dumped to json instead of pickle
'''

import argparse
from datetime import datetime
import json
import logging
import os

import numpy as np

def json_encoder(obj):
    return_val = None
    if isinstance(obj, np.integer):
        return_val = int(obj)
    elif isinstance(obj, np.floating):
        return_val = float(obj)
    elif isinstance(obj, np.ndarray):
        return_val = obj.tolist()
    elif isinstance(obj, datetime):
        return_val = obj.isoformat()
    else:
        raise TypeError
    return return_val

def convert_to_icd9(dx_str):
    return_val = None
    if dx_str.startswith('E'):
        if len(dx_str) > 4:
            return_val = dx_str[:4] + '.' + dx_str[4:]
        else:
            return_val = dx_str
    else:
        if len(dx_str) > 3:
            return_val = dx_str[:3] + '.' + dx_str[3:]
        else:
            return_val = dx_str
    return return_val

def convert_to_3digit_icd9(dx_str):
    return_val = None
    if dx_str.startswith('E'):
        if len(dx_str) > 4:
            return_val = dx_str[:4]
        else:
            return_val = dx_str
    else:
        if len(dx_str) > 3:
            return_val = dx_str[:3]
        else:
            return_val = dx_str
    return return_val

def process(admission_file, diagnosis_file, ccs_map_file, out_dir):
    # load in dictionary with ccs code keys and ICD9 code values
    with open(ccs_map_file, 'r') as ccs_icd_file:
        icd_ccs_dx = json.load(ccs_icd_file)
    logging.debug("Loaded ccs file containing icd9 codes.")

    logging.info('Building pid-admission mapping, admission-date mapping')
    pid_adm_map = {}
    adm_date_map = {}
    with open(admission_file, 'r')as infd:
        infd.readline()
        for line in infd:
            tokens = line.strip().split(',')
            pid = int(tokens[1])
            adm_id = int(tokens[2])
            adm_time = datetime.strptime(tokens[3], '%Y-%m-%d %H:%M:%S')
            adm_date_map[adm_id] = adm_time
            if pid in pid_adm_map:
                pid_adm_map[pid].append(adm_id)
            else:
                pid_adm_map[pid] = [adm_id]

    logging.info('Building admission-dxList mapping')
    adm_dx_map = {}
    infd = open(diagnosis_file, 'r')
    infd.readline()
    for line in infd:
        tokens = line.strip().split(',')
        adm_id = int(tokens[2])

        ### swap commented lines if you want to use the entire ICD9 digits.
        dx_str = 'D_' + convert_to_icd9(tokens[4][1:-1])
        #dx_str = 'D_' + convert_to_3digit_icd9(tokens[4][1:-1])
        if adm_id in adm_dx_map:
            adm_dx_map[adm_id].append(dx_str)
        else: adm_dx_map[adm_id] = [dx_str]
    infd.close()

    logging.info('Building pid-sortedVisits mapping')
    pid_seq_map = {}
    for pid, adm_id_list in pid_adm_map.items():
        if len(adm_id_list) < 2:
            continue
        sorted_list = sorted([(adm_date_map[adm_id], adm_dx_map[adm_id]) \
            for adm_id in adm_id_list])
        pid_seq_map[pid] = sorted_list

    logging.info('Building pids, dates, strSeqs')
    pids = []
    dates = []
    seqs = []
    for pid, visits in pid_seq_map.items():
        pids.append(pid)
        seq = []
        date = []
        for visit in visits:
            date.append(visit[0])
            seq.append(visit[1])
        dates.append(date)
        seqs.append(seq)

    logging.info('Converting strSeqs to intSeqs, and making types')
    types = {}
    ccs_types = {}
    new_seqs = []
    lab_seqs = []
    # patient level (list of lists)
    for patient in seqs:
        # create blank patient list
        new_patient = []
        ccs_patient = []
        # visit level (list of ints)
        for visit in patient:
            # create blank visit list
            new_visit = []
            ccs_visit = []
            # code level (int)
            for code in visit:
                # translate a D_###.## ICD9 code to ### CCS code
                ccs_code = [int(k) for k, v in icd_ccs_dx.items()
                            if code[2:].replace('.', '') in v]
                if not ccs_code:
                    logging.info('Could not find code %s in CCS dict.', code)
                    ccs_code = code
                else:
                    ccs_code = ccs_code[0]

                # keep track of codes we've seen
                if code in types:
                    new_visit.append(types[code])
                # if new code, add to dict to keep track
                else:
                    types[code] = len(types)
                    new_visit.append(types[code])
                if ccs_code not in ccs_types:
                    ccs_types[ccs_code] = len(ccs_types)
                ccs_visit.append(ccs_types[ccs_code])
            # add visit list to patient
            new_patient.append(new_visit)
            ccs_patient.append(ccs_visit)
        # add patient to list of all patients
        new_seqs.append(new_patient)
        lab_seqs.append(ccs_patient)

    ### seqs = [patient[visit[], visit[]...], patient[visit[]...]]
    # get random permutation of pids
    np.random.seed(12345)
    indices = np.random.permutation(len(pids))
    # split into three groups approximately 60%, 20%, 20%
    ind_train = len(pids)*3//5
    ind_valid = ind_train + (len(pids) - ind_train)//2
    # test is whatever is left (through to end of list)

    # get indices for each group
    train = indices[:ind_train]
    valid = indices[ind_train:ind_valid]
    tests = indices[ind_valid:]

    # get broken out lists of pids
    pids_arr = np.array(pids)
    tr_pids = list(pids_arr[train])
    va_pids = list(pids_arr[valid])
    te_pids = list(pids_arr[tests])
    # don't wait for garbage collect
    del pids_arr

    # get broken out lists of seqs
    seqs_arr = np.array(new_seqs)
    tr_seqs = list(seqs_arr[train])
    va_seqs = list(seqs_arr[valid])
    te_seqs = list(seqs_arr[tests])
    del seqs_arr

    # get broken out lists of dates
    date_arr = np.array(dates)
    tr_date = list(date_arr[train])
    va_date = list(date_arr[valid])
    te_date = list(date_arr[tests])
    del date_arr

    # get broken out lists of ccs seqs
    labl_arr = np.array(lab_seqs)
    tr_labl = list(labl_arr[train])
    va_labl = list(labl_arr[valid])
    te_labl = list(labl_arr[tests])
    del labl_arr

    # write outputs for train, valid and test arrays. These will be "visits"
    # write second copy of seqs, dates with CCS codes.  These will be "labels"

    with open(os.path.join(out_dir, 'visit_types.json'), 'w', encoding='utf8') as outfile:
        json.dump(types, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'label_types.json'), 'w', encoding='utf8') as outfile:
        json.dump(ccs_types, outfile, indent=2, default=json_encoder)
    logging.info("# visit codes: %d, # label codes: %d", len(types), len(ccs_types))

    with open(os.path.join(out_dir, 'pids.train.json'), 'w', encoding='utf8') as outfile:
        json.dump(tr_pids, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'pids.valid.json'), 'w', encoding='utf8') as outfile:
        json.dump(va_pids, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'pids.test.json'), 'w', encoding='utf8') as outfile:
        json.dump(te_pids, outfile, indent=2, default=json_encoder)

    with open(os.path.join(out_dir, 'seqs_visit.train.json'), 'w', encoding='utf8') as outfile:
        json.dump(tr_seqs, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'seqs_visit.valid.json'), 'w', encoding='utf8') as outfile:
        json.dump(va_seqs, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'seqs_visit.test.json'), 'w', encoding='utf8') as outfile:
        json.dump(te_seqs, outfile, indent=2, default=json_encoder)

    with open(os.path.join(out_dir, 'date.train.json'), 'w', encoding='utf8') as outfile:
        json.dump(tr_date, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'date.valid.json'), 'w', encoding='utf8') as outfile:
        json.dump(va_date, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'date.test.json'), 'w', encoding='utf8') as outfile:
        json.dump(te_date, outfile, indent=2, default=json_encoder)

    with open(os.path.join(out_dir, 'seqs_label.train.json'), 'w', encoding='utf8') as outfile:
        json.dump(tr_labl, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'seqs_label.valid.json'), 'w', encoding='utf8') as outfile:
        json.dump(va_labl, outfile, indent=2, default=json_encoder)
    with open(os.path.join(out_dir, 'seqs_label.test.json'), 'w', encoding='utf8') as outfile:
        json.dump(te_labl, outfile, indent=2, default=json_encoder)

def parse_arguments(parser):
    parser.add_argument(\
        'admission_file',
        type=str,
        help='The path to the admission file from the MIMIC database.')
    parser.add_argument(\
        'diagnosis_file',
        type=str,
        help='The path to the diagnosis file from the MIMIC database.')
    parser.add_argument(\
        'ccs_map_file',
        type=str,
        help='The path to the mapping from ICD to CCS codes in JSON format.')
    parser.add_argument(\
        'out_dir',
        type=str,
        help='The path to the output directory.')
    parser.add_argument('-v', '--verbose', action='store_true',\
        help='Show verbose output.')
    args = parser.parse_args()
    return args

def main():
    parser = argparse.ArgumentParser()
    args = parse_arguments(parser)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.warning("Set logging to debug.")
    else:
        logging.basicConfig(level=logging.INFO)

    process(args.admission_file, args.diagnosis_file, args.ccs_map_file, args.out_dir)

if __name__ == '__main__':
    main()
