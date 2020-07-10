
''' This project uses the MIMIC-III dataset, which is freely available, 
but requires credentialling through CITI and MIT.  If you have not 
already completed the process to get access to the database, 
see physionet https://physionet.org/content/mimiciii/1.4/, 
you need to complete that before you can run this project: 

This project will walk you through an implementation using EMR ICD-9
data codes from the MIMIC dataset to predict future hospital events.
Specifically, it uses the ADMISSIONS.csv files which contain diagnosis
codes.  Additional codes in the MIMIC dataset include procedure and drug
codes.

The ways in which you could extend this include modifying this model
to predict timing of events, predict a specific type of diagnosis only,
or extend it to predict drug and procedure events in addition to 
diagnostics.  

This project was built from the work detailed in:

	Doctor AI: Predicting Clinical Events via Recurrent Neural Networks  
	Edward Choi, Mohammad Taha Bahadori, Andy Schuetz, Walter F. 
	Stewart, Jimeng Sun  arXiv preprint arXiv:1511.05942

	Medical Concept Representation Learning from Electronic Health 
	Records and its Application on Heart Failure Prediction  
	Edward Choi, Andy Schuetz, Walter F. Stewart, Jimeng Sun  
	arXiv preprint arXiv:1602.03686
	
And uses the codebase developed and available here:
https://github.com/mp2893/doctorai

Good luck!

-Data Science Course Directors
'''

'''This module automates the unpacking of the raw MIMIC-III data.
	It requires that you've downloaded the zip folder into the directory
	with all the scripts required to run the project.
	
	inputs:
		- (optional) name for unzipped folder
		- (optional) verbose output
	output:
		- unzipped folder with Admissions and Diagnoses datasets
'''

import os
import sys
import logging
import zipfile
import gzip
import shutil
import getopt


if __name__ == '__main__':
	argv = sys.argv[1:]  # read in command line arguments
	mimic_unzipped_data = "mimic-iii-dataset"
	isdebug = False  # flag used to set logging level
	try:
		opts, args = getopt.getopt(argv,"n:v",["dirname=", "verbose"])
	except getopt.GetoptError:
		print('unpack_mimic.py -n= <name of output directory>'
			  '-v <verbose output> ')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('unpack_mimic.py -n= <name of output directory> '
				   '-v <verbose output> ')
			sys.exit()
		elif opt in ("-n", "--dirname"):
			mimic_unzipped_data = arg
		elif opt in ("-v", "--verbose"):
			isdebug = True
			logging.basicConfig(level=logging.DEBUG)
			print("Set logging to debug.")
	if not isdebug:
		logging.basicConfig(level=logging.INFO)

	mimic_default_download = "mimic-iii-clinical-database-1.4.zip"

	needed_files = ["ADMISSIONS.csv", "DIAGNOSES_ICD.csv"]
	input_filepaths = [os.path.join(mimic_unzipped_data, f_gz) 
													for f_gz in needed_files]

	# Check if mimic folder is there, unzip and unpack files we need.
	logging.info("Beginning to extract the mimic datafiles...")
	if not os.path.exists(mimic_default_download):
		raise IOError(f"Couldn't locate mimic zip file. "
					  f"Ensure mimic data is in default dir "
					  f"with name: {mimic_default_download}\n"
					  f"You can download it from here: "
					  f"https://physionet.org/content/mimiciii/1.4/")
		sys.exit(-1)
	elif os.path.isdir(mimic_unzipped_data):
		files_exist = [f for f in os.listdir(mimic_unzipped_data) 
						if os.isfile(ps.path.join(mimic_unzipped_data, f))]
		if not files_exist:
			logging.warn(f"Empty mimic data directory, "
				f"remove or rename {mimic_unzipped_data} directory and retry.")
			sys.exit(-1)
	else:
		logging.debug(f"Unzipping {os.path.abspath(mimic_default_download)}")
		try:
			with zipfile.ZipFile(os.path.abspath(mimic_default_download)) as mimic_zipped:
				mimic_zipped.extractall()
		except OSError:
			logging.warn("Something went wrong unzipping."
							"Check it's not in use and retry.")
			sys.exit(-1)
		logging.debug(f"Renaming {mimic_default_download} "
					   f"directory to {mimic_unzipped_data}...")
		os.rename(mimic_default_download.split(".zip")[0], mimic_unzipped_data)
		
		logging.info("Starting to unzip gz files...")
		for ind, gzipped in enumerate([f + ".gz" for f in input_filepaths]):
			with gzip.open(gzipped, 'rb') as f_gz, \
					  open(needed_files[ind], 'wb') as f_out:
				logging.debug(f"gunzipping {gzipped}...")
				shutil.copyfileobj(f_gz, f_out)

	logging.info("Successfully extracted and unpacked mimic data.")

	preview_data = []
	# open admissions file, read in a line after 2 (to skip column headers)
	with open(needed_files[0], 'r') as admissions:
		target_line = 0
		line_num = 0
		num_lines = 3
		logging.debug(f"reading in lines {target_line} "
					  f"- {num_lines+target_line} from ADMISSIONS...")
		for line in admissions:
			if line_num < target_line:
				line_num = line_num + 1
			elif line_num > target_line + num_lines:
				break
			else:
				preview_data.append(line.split(","))
				line_num = line_num + 1

	print("Preview of the data...")
	for col, row in enumerate(preview_data):
		output = " ".join([x.ljust(5) for x in row])
		print(output+"\n")
	print(".....\n")
	logging.info("Complete. Ready to process data files.")
