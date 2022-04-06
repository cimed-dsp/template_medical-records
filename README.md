# Electronic Medical Records DSP Tutorial

## Overview

This project uses the MIMIC-III dataset, which is available free of cost to users authorized through CITI and MIT.  If you have not yet completed the process to access the database, make sure to complete Step 0 of the tutorial as soon as possible.

We have extended the functionality of the DoctorAI codebase (see below references) to include scripts to help you unpack the data from the MIMIC download, process the raw ICD-9 codes into CCS code categories, train the prediction model, test the prediction model, and then translate the CCS codes back into text from their number representations used for training/testing.

This project will use EMR ICD-9 data codes from the MIMIC dataset to predict future hospital events. Specifically, it uses the ADMISSIONS.csv and DIAGNOSES_ICD.csv files, which contain diagnosis codes.  Additional codes in the MIMIC dataset include procedure and drug codes. While reading the related papers and working through this analysis, you may want to consider the the critical questions for data analysis related to the DSP Course [Competencies](https://cimed-dsp.github.io/competency.html).

## Resources

This project was built from the work detailed in two papers:

Doctor AI: Predicting Clinical Events via Recurrent Neural Networks
Edward Choi, Mohammad Taha Bahadori, Andy Schuetz, Walter F. Stewart, Jimeng Sun
arXiv preprint [arXiv:1511.05942](https://arxiv.org/abs/1511.05942)

Medical Concept Representation Learning from Electronic Health
Records and its Application on Heart Failure Prediction
Edward Choi, Andy Schuetz, Walter F. Stewart, Jimeng Sun
arXiv preprint [arXiv:1602.03686](https://arxiv.org/abs/1602.03686)

And uses the codebase developed and available here:
[https://github.com/mp2893/doctorai](https://github.com/mp2893/doctorai)
(The procedure below will copy a different version of this code.)

This project was written in Python.  For more information and resources for learning the python language, please visit the [Carle Illinois Virtual Library](https://guides.library.illinois.edu/cimed/datascience)
Tags:

- EMR
- Neural Nets
- Prediction
- Python 3
- MIMIC III
- ICD Codes

## Tutorial

### Step 0. Access to MIMIC III Database

The MIMIC III Database is hosted on Physionet and access is controlled by a data group at MIT.  In order to access the MIMIC database, you need to follow these directions:

1. Register for an account on PhysioNet: [https://physionet.org](https://physionet.org/). If you already have a PhysioNet account, log in.
2. Fill out the [MIMIC Request Access Form](https://forms.gle/UAE6PBTNM1S7sqBVA)
3. Register on the CITI program website, selecting “Massachusetts Institute of Technology Affiliates” as your affiliation (not “independent learner”): [https://www.citiprogram.org/index.cfm?pageID=154&icat=0&ac=0](https://www.citiprogram.org/index.cfm?pageID=154&icat=0&ac=0)
4. Generate a PDF of the CITI Completion Certificate showing all modules completed with dates and scores
5. Complete the MIMIC III Credentialed user form by logging into your Physionet account here: [https://physionet.org/login/?next=/settings/credentialing/](https://physionet.org/login/?next=/settings/credentialing/)

On the MIMIC III access form:

- For "Supervisor", please list Ruoqing Zhu
- Provide full contact information
- Course name: Medicine - Data Science Projects
- Course number: BSE 686
- Research summary: provide a succinct summary of what you hope to investigate in general.
- Submit a CITI certificate showing a full completion report (with a list of modules, dates, and scores).  We require the full completion report, not just the list of courses completed.

Failure to provide ALL of the information for the MIMIC III access form on PhysioNet will result in delayed or denied access to the database.  Please proofread your form before submitting.

Once you have AWS and MIMIC-III access you are ready to begin Step 1.

### Step 1. Create your Cloud9 environment

In your browser, open the [AWS at Illinois](https://aws.illinois.edu) page and sign in with your usual Illinois credentials. Once you are redirected to AWS, first set your Region (uper right corner) to Ohio/us-east-2.  Default is N.Virginia/us-east-1. Next, open the [Cloud9 creation form](https://us-east-2.console.aws.amazon.com/cloud9/home/create).

On the first page of the form, give your Cloud9 environment a name (e.g., `<your-net-id>-emr`). Enter a description if you like. Press the "Next step" button.

On the second page of the form, make the following changes: 

- For "Instance type", select "Other Instance Type" and choose `t3.medium` from the dropdown menu.  
- Change "Platform" to "Ubuntu Server 18.04 LTS" 

Press the "Next step" button.

On the third page of the form, scroll to the bottom and press the "Create environment" button. On-screen messages will report progress, and when your environment is ready, you'll see a welcome screen.

#### Using Cloud9

Inside your Cloud9 environment, you will see a panel on the left that shows your files. You can upload a file from your computer by dragging it over this panel and dropping it into the desired folder. You can download a file to your computer by right-clicking on its name and selecting "Download" from the menu that appears. Double-clicking a file will open it for editing in a tab on the right side of the screen.

You'll also see a tab near the bottom of the screen that contains a terminal with a command prompt. Commands in the following steps should be run from the prompt in a terminal tab in your Cloud9 environment.

You can resize and rearrange the panels on the screen, create new terminal tabs and file tabs, and customize your environment in other ways; see [the tour](https://docs.aws.amazon.com/console/cloud9/tutorial-tour-ide) for more information.

To go back to AWS, click the Cloud 9 logo at screen top left to open the top level menu and select `Go To Your Dashboard`.  There is no "shutdown" or "hibernate" button, so when you're done with your processing and want to leave, we recommend downloading or backing up and critical output/results, then simply close the tab.

#### Cloud9 hibernation

Your Cloud9 environment will hibernate if idle for more than 30 minutes or if your AWS session expires. This reduces costs and keeps your Cloud9 environment secure.

Whenever your Cloud9 environment hibernates, you can resume your session by doing the following: First, you can close your old Cloud9 tab. In a new tab, sign in at [AWS at Illinois](https://aws.illinois.edu) and then open your [Cloud9 dashboard](https://us-east-2.console.aws.amazon.com/cloud9/home?region=us-east-2). Press either one of the "Open IDE" buttons on the screen. In your restarted Cloud9 environment, your files will be restored exactly as they were, but any terminal tabs will be reinitialized. You will probably want to change back to your previous working directory (for the tutorial, `cd dsp_emr`) and reactivate your Anaconda environment (`conda activate dsp_emr`).

#### Destroying a Cloud9 environment

When you no longer need your Cloud9 environment, make sure you have another copy of all of your files, and then return to [Cloud9 on AWS](https://us-east-2.console.aws.amazon.com/cloud9/home/), press the "Delete" button, and follow the on-screen prompts.

### Step 2. Clone the code repository and change your working directory

Run the following:  

    git clone https://github.com/cimed-dsp/template_medical-records
    cd template_medical-records

### Step 3. Expand the disk attached to your Cloud9 environment

The command below will reserve 40 GB of storage, which will be enough for the template project and perhaps enough for your independent project, too. If you later find you need more storage, you can run this command again, replacing 40 with the total number of gigabytes you need. Note the `. ` at the beginning of the line is required!
  
    . setup/resize-disk.sh 40

Confirm that you have the expanded storage by using the command:
	
	df -h ~

You should see the Size of your storage, the GB Used, and the available storage remaining, Avail.   Make sure Size is close to 40GB if you used 40 for the resize command.  It may be 39GB; this is fine.

### Step 4. Install the code dependencies using Anaconda

Run the following (again, the `. ` at the beginning of the first line is required):  
  
    . setup/install-conda.sh
    conda env create -f setup/dsp-emr-environment.yml
    conda activate dsp_emr

You should now see `(dsp_emr)` appear on the left side of your command prompt. (You might notice the command output advises you to close and re-open your current shell, but as long as you see `(dsp_emr)` on the left side of your command prompt, you can ignore the message.)

**If at any point you open a new terminal in Cloud9, or if your Cloud9 environment is restarted after hibernation, you will need to run `conda activate dsp_emr` before running any of the files in the `scripts/` directory.**

### Step 5. Download MIMIC dataset files with your PhysioNet credentials

First, confirm that you have access to MIMIC by opening [https://physionet.org/content/mimiciii/1.4/](https://physionet.org/content/mimiciii/1.4/) in your browser.

Look near the top-right corner of the screen, to the left of the "Search" box. If you see your username, you can skip to the next paragraph. Otherwise, if you see "Account", click it to expand the menu and select "Login". Enter your credentials. You will be redirected to a different page, showing your projects. Return to [https://physionet.org/content/mimiciii/1.4/](https://physionet.org/content/mimiciii/1.4/).

Scroll to the "Files" section of the page. If you see a restricted-access warning, you still need to get access to MIMIC-III or sign the data use agreement for this project. Otherwise, you can run the following in your Cloud9 environment, replacing `[username]` with your PhysioNet username and entering your PhysioNet password when prompted:  
  
    wget --user [username] --ask-password -O data/mimic/mimic-iii-clinical-database-1.4.zip \
        https://physionet.org/content/mimiciii/get-zip/1.4/

To confirm the download was successful, run the following command. It should produce `a3eb25060b7dc0843fe2235d81707552` as output.  
  
    md5sum data/mimic/mimic-iii-clinical-database-1.4.zip

### Step 6. Extract the ADMISSIONS and DIAGNOSES_ICD tables from the MIMIC-III zip file to the data directory

Run the following:  
  
    unzip -p data/mimic-iii-clinical-database-1.4.zip mimic-iii-clinical-database-1.4/ADMISSIONS.csv.gz | gunzip > data/mimic/ADMISSIONS.csv
    unzip -p data/mimic-iii-clinical-database-1.4.zip mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz | gunzip > data/mimic/DIAGNOSES_ICD.csv

Later, while working on your independent project, you might be interested in other tables from the MIMIC database. You can produce a list of them by running the following:  
  
    unzip -l data/mimic/mimic-iii-clinical-database-1.4.zip

### Step 7. Create mappings from Clinical Classifications Software (CCS) codes to ICD-9 codes

The diagnoses (`dxref2015.csv`) and procedures (`prref2015.csv`) mapping data are derived from [Healthcare Cost and Utilization Project data](https://www.hcup-us.ahrq.gov/toolssoftware/ccs/ccs.jsp).

Run the following:  
  
    python3 scripts/create_ccs_dict.py data/ccs/dxref2015.csv data/ccs/ 2
    python3 scripts/create_ccs_dict.py data/ccs/prref2015.csv data/ccs/ 2

Look in data/ccs/ for the newly created files, which will have the `.json` extension. Compare the contents of these files with the source `.cvs` files in the same directory. Understand how the `.json` files are structured and how their contents are related to the source `.csv` files.

### Step 8. Create training, testing, and validation inputs for DoctorAI

The `process_mimic.py` script reads visit data, maps diagnosis codes, and partitions the patients into sets; for each set, it will create files containing the patient ids (`pids.*`), patient visit dates (`date.*`), diagnostic codes (`seqs_visit.*`) and their labels (`seqs_labels.*`).

Run the following:  
  
    python3 scripts/process_mimic.py data/mimic/ADMISSIONS.csv \
        data/mimic/DIAGNOSES_ICD.csv data/ccs/dxref2015.json data/mimic/

### Step 9. Train a DoctorAI model

The model will take in 4894 diagnostic codes of one visit and predicts 273 CCS codes for the next visit. The training will use 10 epochs. `python3 scripts/doctor_ai.py -h` will print details about the default structure of the model.

Run the following (the `THEANO_FLAGS` portion of the command below suppresses [a warning message that's safe to ignore](https://github.com/lvapeab/nmt-keras/issues/66)):  
  
    THEANO_FLAGS='optimizer_excluding=scanOp_pushout_output' python3 \
        scripts/doctor_ai.py data/mimic/seqs_visit.train.json \
        data/mimic/seqs_visit.test.json data/mimic/seqs_visit.valid.json \
        4894 data/mimic/seqs_label.train.json data/mimic/seqs_label.test.json \
        data/mimic/seqs_label.valid.json 273 data/mimic/model_processed_data --verbose

### Step 10. Predict the top 30 CCS codes for the subsequent visits for the patients in the test set

Run the following:  
  
    python3 scripts/test_doctor_ai.py data/mimic/model_processed_data.9.npz \
        data/mimic/seqs_visit.test.json data/mimic/seqs_label.test.json \
        [200,200] --output_file data/mimic/predictions_processed_data.test.json --verbose

### Step 11. Convert the prediction outputs into two readable files of CCS codes

One file will contain the top 30 predicted codes (`results_processed_data.predictions.csv`) and the other will contain the actual observed CCS codes (`results_processed_data.actuals.csv`).

Run the following:  
  
    python3 scripts/translate_codes_to_text.py data/mimic/label_types.json \
        data/ccs/dxref2015_text.json \
        data/mimic/predictions_processed_data.test.json \
        data/mimic/results_processed_data.predictions.csv \
        data/mimic/results_processed_data.actuals.csv -v

## Project Extensions and Future Directions

There are many possible directions to take this project.  In general, you could look to update or extend the model to a different ML technique, which would require a bit more work behind the scenes to develop and test.  On the other hand, you could also look to apply this approach to other datasets from EMR, as long as you can de-identify and format the raw information like the csv's provided in the EMR.  This would require more effort in pre-processing the data.

The ways in which you could extend this project include modifying this model to predict timing of events, predict a specific type of diagnosis only, or extend it to predict drug and procedure events in addition to diagnostics.  There have been many dozens/hundreds of papers published using this dataset ( [MIMIC III on Scopus](https://www.scopus.com/results/results.uri?src=s&st1=&st2=&sot=b&sdt=b&sl=25&s=TITLE-ABS-KEY%20(MIMIC-III)&origin=searchbasic) ) which you are also encouraged to consider as inspiration for other possible directions.

Another possibility would be to adapt the model to look for very specific conditions as an early warning flag instead of predicting all possible future codes.  This would require modification of the pre-processing of the data provided, as well as an extension of the interpretation of the model's prediction output to make it more specific to the desired output.

Yet another possibility would be to change the focus of the model from diagnostic codes to drug codes or procedure codes, to see if there is any predictive model that might work for drugs or procedures in addition to diagnoses.

This model is relatively fast to train, so feel free to explore these or other options.
