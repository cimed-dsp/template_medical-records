'''This module translates codes used by the model to CCS text descriptions.
First, it has to go from number -> CCS code, then from
CCS code -> text description of CCS code.

inputs:
    -ccs file.  Use "label_types.json" from process_mimic.py.
    -input file of integer codes.  Use output from test_doctor_ai.py.
    -output file name.

outputs:
    two csv files: one with the descriptions of CCS codes that occurred,
    and the other with a list of predicted codes.
'''


import argparse
import csv
import json
import logging
import sys

def translate_numerics(ccs_label_types_file, inputs_predictions_file):
    '''
    Converts the test_doctor_ai outputs from numeric codes to ccs codes.
    '''
    logging.debug("opening {ccs code : int} and [[int, int, int],...] actuals and preds...")
    # load dicts
    with open(ccs_label_types_file, 'r') as infile:
        ccs_dict = json.load(infile)
    with open(inputs_predictions_file, 'rb') as infile:
        input_dict = json.load(infile)

    # list of lists containing int codes from labels
    actuals = input_dict['inputs']

    # list of lists containing 30 prediction ints from labels and model output
    preds = list(map(list, input_dict['predictions']))

    logging.debug("mapping actual visit ints to ccs...")
    ccs_actuals = []
    for seq in actuals:
        ccs_actuals.append(\
            [[int(k) for k, val in ccs_dict.items() if val == num][0] for num in seq])

    logging.debug("mapping predicted ints to ccs...")
    ccs_preds = []
    for seq in preds:
        ccs_preds.append(\
            [[int(k) for k, val in ccs_dict.items() if val == num][0] for num in seq])

    return (ccs_actuals, ccs_preds)

def load_ccs_text_dx(dxref_text_file):
    '''
    Loads the ccs descriptions.
    '''
    logging.debug("opening ccs text dict...")
    try:
        with open(dxref_text_file, 'r') as ccs_text_file:
            ccs_text_dx = json.load(ccs_text_file)
        logging.debug("loaded ccs file containing text descriptions.")
    except FileNotFoundError:
        logging.error('Could not find %s', dxref_text_file)
        sys.exit(2)

    return ccs_text_dx

def output_text_codes(ccs_codes, ccs_text_dx):
    '''
    Converts ccs codes to ccs descriptions.
    '''
    pred_diagnoses = []
    logging.debug("iterating through lists of ccs codes to map to text...")
    for seq in ccs_codes:
        pred_diagnoses.append(list(map(lambda x: ccs_text_dx.get(str(x)), seq)))

    return pred_diagnoses

def parse_arguments(parser):
    parser.add_argument(\
        'ccs_file',
        type=str,
        help='The path to the JSON label types file from process_mimic.py.')
    parser.add_argument(\
        'dxref_text_file',
        type=str,
        help='The path to the JSON dxref text file from create_ccs_dict.py.')
    parser.add_argument(\
        'inputs_predictions_file',
        type=str,
        help='The path to the JSON predictions file from test_doctor_ai.py.')
    parser.add_argument(\
        'predictions_output_file',
        type=str,
        help='The path to the output file that will contain text descriptions for predicted codes.')
    parser.add_argument(\
        'actuals_output_file',
        type=str,
        help='The path to the output file that will contain text descriptions for actual codes.')
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

    logging.info("beginning translation of integers to ccs codes...")
    actual_ccs_codes, predicted_ccs_codes = translate_numerics(\
        args.ccs_file, args.inputs_predictions_file)
    logging.info("loading dxref_text_file...")
    ccs_text_dx = load_ccs_text_dx(args.dxref_text_file)
    logging.info("beginning translation of predicted ccs codes to text descriptions...")
    prediction_descriptions = output_text_codes(predicted_ccs_codes, ccs_text_dx)
    logging.info("beginning translation of actual ccs codes to text descriptions...")
    actual_descriptions = output_text_codes(actual_ccs_codes, ccs_text_dx)

    logging.info("writing text descriptions of predictions to csv...")
    with open(args.predictions_output_file, 'w', newline="") as outfile:
        pwriter = csv.writer(outfile)
        pwriter.writerows(prediction_descriptions)
    with open(args.actuals_output_file, 'w', newline="") as outfile:
        awriter = csv.writer(outfile)
        awriter.writerows(actual_descriptions)
    logging.info("Complete.")

if __name__ == '__main__':
    main()
