'''This module translates codes used by the model back out to something
readable. First, it has to go from number -> CCS code, then from 
CCS code -> text description of CCS code.  Requires the dxref text dictionary
from createCCSdict.py be in the current directory.

inputs:
	-ccs file.  Use "<whatever file name>_label.types" from process_mimic.py
	-input file of integer codes.  Use <whatever file name> from testDoctorAI.
	-output file name.
	
outputs:
	two csv files: one with the descriptions of CCS codes that occurred, 
	and the other with a list of predicted codes.
'''


try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
import os
import sys
import getopt
import numpy as np
import logging
import csv

def translateNumerics(ccs, inputs):
	'''
	
	'''
	logging.debug("opening {ccs code : int} and [[int, int, int],...] actuals and preds...")
	# unpickle dicts
	with open(ccs, 'rb') as pickled_ccs, open(inputs, 'rb') as pickled_ins:
		ccs_dict = pickle.load(pickled_ccs)
		input_dict = pickle.load(pickled_ins)
	
	# list of lists containing int codes from labels
	actuals = input_dict['inputs']
	
	# list of lists containing 30 prediction ints from labels and model output
	preds = list(map(list, input_dict['predictions']))
	
	logging.debug("mapping actual visit ints to ccs...")
	ccs_actuals = []
	for seq in actuals:
		ccs_actuals.append([[k for k,val in ccs_dict.items() if val == num][0] for num in seq])
		
	logging.debug("mapping predicted ints to ccs...")
	ccs_preds = []
	for seq in preds:
		ccs_preds.append([[k for k,val in ccs_dict.items() if val == num][0] for num in seq])
	
	return (ccs_actuals, ccs_preds)

def outputTextCodes(ccs_codes):
	'''
	
	'''
	logging.debug("opening ccs text dict...")
	try: 
		TODO REMOVE HARDCODED PATH?
		with open('dxref2015_text.dat', 'rb') as ccs_text_file:
			ccs_text_dx = pickle.load(ccs_text_file)
		logging.debug("loaded ccs file containing text descriptions.")
	except FileNotFoundError:
		logging.error(f"Need 'dxref2015_text.dat' in directory: {os.getcwd()}")
		sys.exit(2)
	
	pred_diagnoses = []
	logging.debug("iterating through lists of ccs codes to map to text...")
	for seq in ccs_codes:
		pred_diagnoses.append(list(map(ccs_text_dx.get, seq)))
	
	return pred_diagnoses
	
	

if __name__ == "__main__":
	argv = sys.argv[1:]
	
	# keys = CCS code, values = integers.  Use the _label.type file
	ccsFile = ""
	# dict of lists of integers
	inputFile = ""
	# path to save output
	outFile  = ""
	isdebug = False
	try:
		opts, args = getopt.getopt(argv,"hvc:i:o:",["help", "verbose", "ccsFile=", "inputFile=", "outFile="])
	except getopt.GetoptError:
		print('translateCodesToText.py -c <path of pickled ccs code dict from process_mimic> -i <path to pickled input dict to be translated> -o <name of output files> -v <verbose output> ')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('translateCodesToText.py -c <path of pickled ccs code dict from process_mimic> -i <path to pickled input dict to be translated> -o <name of output files> -v <verbose output> ')
			sys.exit()
		elif opt in ("-c", "--ccsFile"):
			ccsFile = arg
		elif opt in ("-i", "--inputFile"):
			inputFile = arg
		elif opt in ("-o", "--output"):
			outFile = arg
		elif opt in ("-v", "--verbose"):
			isdebug = True
			logging.basicConfig(level=logging.DEBUG)
			logging.warning("Set logging to debug.")
	if not isdebug:
		logging.basicConfig(level=logging.INFO)
		
	if not all((ccsFile, inputFile, outFile)):
		logging.error("must provide a ccsFile, inputFile, and output filename!")
		print('translateCodesToText.py -c <path of pickled ccs code dict from process_mimic> -i <path to pickled input dict to be translated> -o <name of output files> -v <verbose output> ')
		sys.exit(2)
	
	logging.info("beginning translation of integers to ccs codes...")
	actual_ccs_codes, predicted_ccs_codes = translateNumerics(ccsFile, inputFile)
	logging.info("beginning translation of predicted ccs codes to text descriptions...")
	prediction_descriptions = outputTextCodes(predicted_ccs_codes)
	logging.info("beginning translation of actual ccs codes to text descriptions...")
	actual_descriptions = outputTextCodes(actual_ccs_codes)
	
	if outFile != "":
		logging.info("writing text descriptions of predictions to csv...")
		with open(outFile+'.csv', 'w', newline="") as f, open(outFile+'_actual.csv', 'w', newline="") as g:
			pwriter = csv.writer(f)
			awriter = csv.writer(g)
			pwriter.writerows(prediction_descriptions)
			awriter.writerows(actual_descriptions)
		logging.info("Complete.")
	