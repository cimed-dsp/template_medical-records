# Electronic Medical Records DSP


https://us-west-2.console.aws.amazon.com/cloud9/home/create
Give name (e.g., <netid>-emr)
Next step button

Change Platform to Ubuntu Server 18.04 LTS; otherwise, accept defaults (create new ec2 instance, t2.micro, 30 min hibernate, awsserviceroleforawscloud9)
Next step button

Create environment button



if at any point you see a logged out message in C9, open a separate tab, log in at aws.illinois.edu, then refresh the C9 tab



## Overview

This project uses the MIMIC-III dataset, which is freely available, but requires credentialling through CITI and MIT.  If you have not already completed the process to get access to the database, see physionet [https://physionet.org/content/mimiciii/1.4/](https://physionet.org/content/mimiciii/1.4/), you need to complete that before you can run this project.

This project will walk you through an implementation using EMR ICD-9 data codes from the MIMIC dataset to predict future hospital events. Specifically, it uses the ADMISSIONS.csv files which contain diagnosis codes.  Additional codes in the MIMIC dataset include procedure and drug codes.

## Resources

This project was built from the work detailed in:

``` text
Doctor AI: Predicting Clinical Events via Recurrent Neural Networks
Edward Choi, Mohammad Taha Bahadori, Andy Schuetz, Walter F. Stewart, Jimeng Sun
arXiv preprint arXiv:1511.05942
```

``` text
Medical Concept Representation Learning from Electronic Health
Records and its Application on Heart Failure Prediction
Edward Choi, Andy Schuetz, Walter F. Stewart, Jimeng Sun
arXiv preprint arXiv:1602.03686
```

And uses the codebase developed and available here:
[https://github.com/mp2893/doctorai](https://github.com/mp2893/doctorai)
(PROCEDURE BELOW WILL COPY A VERSION OF THIS CODE)

## Tutorial

Create AWS C9. Following commands should be run from prompt in C9.

1. Clone and change to the EMR DSP code repository directory

TODO create public repo
    ``` bash
    git clone https://github.com/CICOM/DSP-EMR.git...
    cd DSP-EMR
    ```

2. Expand the disk attached to your C9. The command below will reserve 40 GB of storage, which will be enough for the template project and perhaps enough for your independent project, too. If you later find you need more storage, you can run this command again, replacing 40 with the number of gigabytes you need.

    ```bash
    sh setup/resize-disk.sh 40
    ```

3. Install the code dependencies using Anaconda.

    ``` bash
    sh setup/install-conda.sh
    conda env create -f dsp-emr-environment.yml
    conda activate dsp_emr
    ```

    At this point, you should see `(dsp_emr)` appear on the left side of your command prompt.

    If at any point you open a new terminal in C9, you will need to run `conda activate dsp_emr` before running any of the files in the `scripts/` directory.

4. Download MIMIC dataset files with your credentialed physionet `[username]` and `[password]`

open https://physionet.org/content/mimiciii/1.4/ in browser
near top-right corner, if you see "Account", click to expand menu and select Login; enter credentials; you'll be redirected to a different page; go back to URL above
Once there, scroll to the bottom to the “Files” section. If the page shows a restricted-access warning, you need to get access to MIMIC-III or sign the data use agreement for this project. Otherwise, you should see the following:

    ``` bash
    wget --user [username] --ask-password -O data/mimic/mimic-iii-clinical-database-1.4.zip \
        https://physionet.org/content/mimiciii/get-zip/1.4/
    md5sum mimic-iii-clinical-database-1.4.zip
    # a3eb25060b7dc0843fe2235d81707552  mimic-iii-clinical-database-1.4.zip
    ```

5. Extract the ADMISSIONS and DIAGNOSES_ICD tables from the MIMIC-III zip file to the current directory.

unzip -l data/mimic/mimic-iii-clinical-database-1.4.zip

unzip -p data/mimic/mimic-iii-clinical-database-1.4.zip mimic-iii-clinical
-database-1.4/ADMISSIONS.csv.gz  | gunzip > data/mimic/ADMISSIONS.csv

again for DIAGNOSES_ICD.csv


6. Create dictionaries that map between Clinical Classifications Software (CCS) codes and ICD-9 codes diagnoses (`dxref2015.csv`) and procedures (`prref2015.csv`). The mapping data is derived from [here](https://www.hcup-us.ahrq.gov/toolssoftware/ccs/ccs.jsp)

    ``` bash
    python3 scripts/create_ccs_dict.py data/ccs/dxref2015.csv data/ccs/ 2
    python3 scripts/create_ccs_dict.py data/ccs/prref2015.csv data/ccs/ 2
    ```

    Look in data/ccs/ for the newly created files, which will have the `.json` extension. Compare the contents of these files with the source `.cvs` files in the same directory. Understand how the `.json` files are structured and how their contents are related to the source `.csv` files.

7. Create training, testing, and validation sets of inputs to DoctorAI by reading in visit data, mapping diagnosis codes, partition the patients between sets, and for each set, printing out object files that contain patient ids (`_pids.*`), patient visit dates (`_dates.*`), diagnostic codes (`_seqs_visit.*`) and their labels (`_seqs_labels.*`) per patient visit

    ``` bash
    python3 scripts/process_mimic.py data/mimic/ADMISSIONS.csv data/mimic/DIAGNOSES_ICD.csv data/ccs/dxref2015.json data/mimic/
    ```

8. Train DoctorAI model that take in 4894 diagnostic codes of one visit and predict 273 CCS codes for the next visit for 10 epochs. Use `python3 doctorAI.py -h` for more details about the default structure of the model.

    ``` bash
    python3 doctorAI.py processed_data_seqs_visit 4894 processed_data_seqs_label 273 \
        model_processed_data --verbose
    ```

9. Predict top 30 CCS codes for the subsequent visits for the patients in the test set

    ``` bash
    python3 testDoctorAI.py model_processed_data.9.npz \
        processed_data_seqs_visit.test processed_data_seqs_label.test \
        [200,200] --output_file predictions_processed_data.test --verbose
    ```

10. Convert prediction data object into two readable files of CCS codes, the top 30 predicted codes (`*.csv`) and the observed CCS codes that occurred (`*_actual.csv.`)

    ``` bash
    python3 translateCodesToText.py -c processed_data_label.types \
        -i predictions_processed_data.test.dat -o results_processed_data.test -v
    ```

## Extensions

The ways in which you could extend this include modifying this model to predict timing of events or to predict a specific type of diagnosis only, or extending it to predict drug and procedure events in addition to diagnostics.

MANAGING C9 COSTS; HIBERNATION
UPLOADING AND DOWNLOADING FILES
CLEANING UP ENVIRONMENT
