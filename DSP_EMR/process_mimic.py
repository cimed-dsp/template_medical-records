'''This script processes MIMIC-III dataset and builds longitudinal diagnosis records for patients with at least two visits.
The output data are cPickled, and suitable for training Doctor AI or RETAIN
Written by Edward Choi (mp2893@gatech.edu)
Usage: Put this script to the foler where MIMIC-III CSV files are located. Then execute the below command.
python process_mimic.py ADMISSIONS.csv DIAGNOSES_ICD.csv <output file> 

-inputs:
	-ADMISSIONS.csv file from MIMIC
	-DIAGNOSES_ICD.csv file from MIMIC 
	-output file name.
	
-outputs
	-<output file>.pids: List of unique Patient IDs. Used for intermediate processing
	-<output file>.dates: List of List of Python datetime objects. The outer List is for each patient. The inner List is for each visit made by each patient
	-<output file>.seqs: List of List of List of integer diagnosis codes. The outer List is for each patient. The middle List contains visits made by each patient. The inner List contains the integer diagnosis codes that occurred in each visit
	-<output file>.types: Python dictionary that maps string diagnosis codes to integer diagnosis codes.

# Edited 2/6/2020 Eliot Bethke
# -updated print syntax to python3 compat
# -updated 'iteritems' syntax to 'items' to python3 compat
# -added train, valid, test splitting by 60/20/20 fixed percentages
# -imports ccs code dictionary with 'CCS code' (key) : [ICD9 codes...] (value)
'''


import sys
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
from datetime import datetime
import numpy as np
import getopt
import logging
import os


def convert_to_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4] + '.' + dxStr[4:]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3] + '.' + dxStr[3:]
		else: return dxStr
	
def convert_to_3digit_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3]
		else: return dxStr



	
def main(admissionFile, diagnosisFile, outFile):
	# load in dictionary with ccs code keys and ICD9 code values
	try: 
		with open('dxref2015.dat', 'rb') as ccs_icd_file:
			icd_ccs_dx = pickle.load(ccs_icd_file)
		logging.debug("Loaded ccs file containing icd9 codes.")
	except FileNotFoundError:
		logging.error(f"Need 'dxref2015.dat' in directory: {os.getcwd()}")
		sys.exit(1)
	
	logging.info( 'Building pid-admission mapping, admission-date mapping')
	pidAdmMap = {}
	admDateMap = {}
	with open(admissionFile, 'r')as infd:
		infd.readline()
		for line in infd:
			tokens = line.strip().split(',')
			pid = int(tokens[1])
			admId = int(tokens[2])
			admTime = datetime.strptime(tokens[3], '%Y-%m-%d %H:%M:%S')
			admDateMap[admId] = admTime
			if pid in pidAdmMap: 
				pidAdmMap[pid].append(admId)
			else: 
				pidAdmMap[pid] = [admId]

	logging.info( 'Building admission-dxList mapping')
	admDxMap = {}
	infd = open(diagnosisFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		admId = int(tokens[2])
		
		### swap commented lines if you want to use the entire ICD9 digits.
		dxStr = 'D_' + convert_to_icd9(tokens[4][1:-1]) 
		#dxStr = 'D_' + convert_to_3digit_icd9(tokens[4][1:-1])
		if admId in admDxMap: admDxMap[admId].append(dxStr)
		else: admDxMap[admId] = [dxStr]
	infd.close()

	logging.info( 'Building pid-sortedVisits mapping')
	pidSeqMap = {}
	for pid, admIdList in pidAdmMap.items():
		if len(admIdList) < 2: 
			continue
		sortedList = sorted([(admDateMap[admId], admDxMap[admId]) 
									for admId in admIdList])
		pidSeqMap[pid] = sortedList
	
	logging.info( 'Building pids, dates, strSeqs')
	pids = []
	dates = []
	seqs = []
	for pid, visits in pidSeqMap.items():
		pids.append(pid)
		seq = []
		date = []
		for visit in visits:
			date.append(visit[0])
			seq.append(visit[1])
		dates.append(date)
		seqs.append(seq)
	
	logging.info( 'Converting strSeqs to intSeqs, and making types')
	types = {}
	ccs_types = {}
	newSeqs = []
	labSeqs = []
	# patient level (list of lists)
	for patient in seqs:
		# create blank patient list
		newPatient = []
		ccsPatient = []
		# visit level (list of ints)
		for visit in patient:
			# create blank visit list
			newVisit = []
			ccsVisit = []
			# code level (int)
			for code in visit:
				# translate a D_###.## ICD9 code to ### CCS code
				ccs_code = [k for k,v in icd_ccs_dx.items() 
							if code[2:].replace('.', '') in v]
				if not ccs_code:
					logging.info(f'Could not find code {code} in CCS dict.')
					ccs_code = code
				else:
					ccs_code = ccs_code[0]
				
				# keep track of codes we've seen
				if code in types:	
					newVisit.append(types[code])
				# if new code, add to dict to keep track
				else:
					types[code] = len(types)
					newVisit.append(types[code])
				if ccs_code not in ccs_types:
					ccs_types[ccs_code] = len(ccs_types)
				ccsVisit.append(ccs_types[ccs_code])
			# add visit list to patient
			newPatient.append(newVisit)
			ccsPatient.append(ccsVisit)
		# add patient to list of all patients
		newSeqs.append(newPatient)
		labSeqs.append(ccsPatient)
		
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
	seqs_arr = np.array(newSeqs)
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
	labl_arr = np.array(labSeqs)
	tr_labl = list(labl_arr[train])
	va_labl = list(labl_arr[valid])
	te_labl = list(labl_arr[tests])
	del labl_arr
	
	
	
	# write pickle for train, valid and test arrays. These will be "visits"
	# write second copy of seqs, dates with CCS codes.  These will be "labels" 
	
	
	# pickle.dump(pids, open(outFile+'.pids', 'wb'), -1)
	# pickle.dump(dates, open(outFile+'.dates', 'wb'), -1)
	# pickle.dump(newSeqs, open(outFile+'.seqs', 'wb'), -1)
	
	pickle.dump(types, open(outFile+'_visit.types', 'wb'), 2)
	pickle.dump(ccs_types, open(outFile+'_label.types', 'wb'), 2)
	logging.info(f"# visit codes:{len(types)}, # label codes:{len(ccs_types)}")
	
	
	pickle.dump(tr_pids, open(outFile+'_pids.train', 'wb'), 2)
	pickle.dump(va_pids, open(outFile+'_pids.valid', 'wb'), 2)
	pickle.dump(te_pids, open(outFile+'_pids.test', 'wb'), 2)
	
	pickle.dump(tr_seqs, open(outFile+'_seqs_visit.train', 'wb'), 2)
	pickle.dump(va_seqs, open(outFile+'_seqs_visit.valid', 'wb'), 2)
	pickle.dump(te_seqs, open(outFile+'_seqs_visit.test', 'wb'), 2)
	
	pickle.dump(tr_date, open(outFile+'_date.train', 'wb'), 2)
	pickle.dump(va_date, open(outFile+'_date.valid', 'wb'), 2)
	pickle.dump(te_date, open(outFile+'_date.test', 'wb'), 2)
	
	pickle.dump(tr_labl, open(outFile+'_seqs_label.train', 'wb'), 2)
	pickle.dump(va_labl, open(outFile+'_seqs_label.valid', 'wb'), 2)
	pickle.dump(te_labl, open(outFile+'_seqs_label.test', 'wb'), 2)
	
	return( (len(types), len(ccs_types)) )




if __name__ == '__main__':
	argv = sys.argv[1:]
	admissionFile = ""
	diagnosisFile = ""
	outFile  = ""
	isdebug = False
	try:
		opts, args = getopt.getopt(argv,"hva:d:o:",["help", "verbose", \
							"admissionFile=", "diagnosisFile=", "outFile="])
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
			admissionFile = arg
		elif opt in ("-d", "--diagnosis"):
			diagnosisFile = arg
		elif opt in ("-o", "--output"):
			outFile = arg
		elif opt in ("-v", "--verbose"):
			isdebug = True
			logging.basicConfig(level=logging.DEBUG)
			logging.warning("Set logging to debug.")
	if not isdebug:
		logging.basicConfig(level=logging.INFO)
	
	if not all((admissionFile, diagnosisFile, outFile)):
		logging.error("Must provide an admission file, a diagnosis file, "
						"and an output file name!")
		print('process_mimic.py -a <name of admission file>'
				'-d <name of diagnosis file> '
				'-o <name of output files> '
				'-v <verbose output> ')
		sys.exit(2)
		
		
	num_visit_codes, num_label_codes = main(admissionFile, diagnosisFile, outFile)
	
	
	