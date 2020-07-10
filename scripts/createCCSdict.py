'''This module creates dictionaries mapping ICD to CCS, and also 
CCS codes to their text descriptions.  You can get the code files here:
https://www.hcup-us.ahrq.gov/toolssoftware/ccs/ccs.jsp

We use the single level csv files for this.  The outputs of these files are
used later in process_mimic.py for creating the label files used to train
the model.

inputs:
	- dxref and prref Single Level files from CCS.
outputs:
	- pickled dict of CCS:ICD9
	- pickled dict of CCS:Description

'''

import os
import sys
import pickle

len_headers = 2
# TODO add file input from command

def get_code_mapping(ccsfile):
	output = ccs_file.split('.')[0]

	with open(ccsfile, 'r') as ref:
		# throw away headers
		for header in range(len_headers):
			throw = ref.readline()
		
		ccs_map = {}
		ccs_translation = {}
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
		print(len(ccs_codes))
		print(ccs_map[1][:10])
		
	# output as pickled dict to be read in and used to 'translate' diagnosis codes in doctorai
	TODO TAKE OUTPUT FILES AS ARGS?
	with open(output+'.dat', 'wb') as outfile, open(output+'_text.dat', 'wb') as outtext:
		pickle.dump(ccs_map, outfile, 2)
		pickle.dump(ccs_translation, outtext, 2)
		
if __name__ == '__main__':	
	TODO REMOVE DEFAULTS
	ccs_files = ['dxref2015.csv', 'prref2015.csv']
	for ccs_file in ccs_files:
		get_code_mapping(ccs_file)
