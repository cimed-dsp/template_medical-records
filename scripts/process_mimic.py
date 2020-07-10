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
# - delinted
'''

import sys
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
from datetime import datetime
import getopt
import logging
import os

import numpy as np

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

def process(admission_file, diagnosis_file, out_file):
    # load in dictionary with ccs code keys and ICD9 code values
    try:
        with open('dxref2015.dat', 'rb') as ccs_icd_file:
            icd_ccs_dx = pickle.load(ccs_icd_file)
        logging.debug("Loaded ccs file containing icd9 codes.")
    except FileNotFoundError:
        logging.error("Need 'dxref2015.dat' in directory: %s", os.getcwd())
        sys.exit(1)

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
                ccs_code = [k for k, v in icd_ccs_dx.items()
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
    indeces = np.random.permutation(len(pids))
    # split into three groups approximately 60%, 20%, 20%
    ind_train = len(pids)*3//5
    ind_valid = ind_train + (len(pids) - ind_train)//2
    # test is whatever is left (through to end of list)

    # get indeces for each group
    train = indeces[:ind_train]
    valid = indeces[ind_train:ind_valid]
    tests = indeces[ind_valid:]

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



    # write pickle for train, valid and test arrays. These will be "visits"
    # write second copy of seqs, dates with CCS codes.  These will be "labels"


    # pickle.dump(pids, open(out_file+'.pids', 'wb'), -1)
    # pickle.dump(dates, open(out_file+'.dates', 'wb'), -1)
    # pickle.dump(new_seqs, open(out_file+'.seqs', 'wb'), -1)

    pickle.dump(types, open(out_file+'_visit.types', 'wb'), 2)
    pickle.dump(ccs_types, open(out_file+'_label.types', 'wb'), 2)
    logging.info("# visit codes: %d, # label codes: %d", len(types), len(ccs_types))


    pickle.dump(tr_pids, open(out_file+'_pids.train', 'wb'), 2)
    pickle.dump(va_pids, open(out_file+'_pids.valid', 'wb'), 2)
    pickle.dump(te_pids, open(out_file+'_pids.test', 'wb'), 2)

    pickle.dump(tr_seqs, open(out_file+'_seqs_visit.train', 'wb'), 2)
    pickle.dump(va_seqs, open(out_file+'_seqs_visit.valid', 'wb'), 2)
    pickle.dump(te_seqs, open(out_file+'_seqs_visit.test', 'wb'), 2)

    pickle.dump(tr_date, open(out_file+'_date.train', 'wb'), 2)
    pickle.dump(va_date, open(out_file+'_date.valid', 'wb'), 2)
    pickle.dump(te_date, open(out_file+'_date.test', 'wb'), 2)

    pickle.dump(tr_labl, open(out_file+'_seqs_label.train', 'wb'), 2)
    pickle.dump(va_labl, open(out_file+'_seqs_label.valid', 'wb'), 2)
    pickle.dump(te_labl, open(out_file+'_seqs_label.test', 'wb'), 2)

def main():
    argv = sys.argv[1:]
    admission_file = ""
    diagnosis_file = ""
    out_file = ""
    isdebug = False
    try:
        opts, args = getopt.getopt(argv, "hva:d:o:", ["help", "verbose",\
            "admission_file=", "diagnosis_file=", "out_file="])
    except getopt.GetoptError:
        print('process_mimic.py -a <name of admission file>'
              '-d <name of diagnosis file> '
              '-o <name of output files> '
              '-v <verbose output> ')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('process_mimic.py -a <name of admission file>'
                  '-d <name of diagnosis file> '
                  '-o <name of output files> '
                  '-v <verbose output> ')
            sys.exit()
        elif opt in ("-a", "--admission"):
            admission_file = arg
        elif opt in ("-d", "--diagnosis"):
            diagnosis_file = arg
        elif opt in ("-o", "--output"):
            out_file = arg
        elif opt in ("-v", "--verbose"):
            isdebug = True
            logging.basicConfig(level=logging.DEBUG)
            logging.warning("Set logging to debug.")
    if not isdebug:
        logging.basicConfig(level=logging.INFO)

    if not all((admission_file, diagnosis_file, out_file)):
        logging.error("Must provide an admission file, a diagnosis file, "
                      "and an output file name!")
        print('process_mimic.py -a <name of admission file>'
              '-d <name of diagnosis file> '
              '-o <name of output files> '
              '-v <verbose output> ')
        sys.exit(2)

    process(admission_file, diagnosis_file, out_file)

if __name__ == '__main__':
    main()
