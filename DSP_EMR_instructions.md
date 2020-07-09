# Electronic Medical Records DSP

## Overview

This project uses the MIMIC-III dataset, which is freely available, but requires credentialling through CITI and MIT.  If you have not already completed the process to get access to the database, see physionet [https://physionet.org/content/mimiciii/1.4/](https://physionet.org/content/mimiciii/1.4/), you need to complete that before you can run this project.

This project will walk you through an implementation using EMR ICD-9 data codes from the MIMIC dataset to predict future hospital events. Specifically, it uses the ADMISSIONS.csv files which contain diagnosis codes.  Additional codes in the MIMIC dataset include procedure and drug codes.

The ways in which you could extend this include modifying this model to predict timing of events, predict a specific type of diagnosis only, or extend it to predict drug and procedure events in addition to diagnostics.  

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

## Tutorial

1. Access your AWS C9 (needs Anaconda)

    ``` bash
    docker run -i -t --rm --name my_anaconda3 -v $(pwd):/home/ubuntu/projects/ \
        -w /home/ubuntu/projects/ continuumio/anaconda3 /bin/bash
    ```

2. Clone and change to the EMR DSP code repository directory

    ``` bash
    git clone https://github.com/CICOM/EMR_DSP.git...
    cd EMR_DSP
    ```

3. Download MIMIC dataset files with your credentialed physionet `[username]` and `[password]`

    ``` bash
    wget --user [username] --ask-password -O mimic-iii-clinical-database-1.4.zip \
        https://physionet.org/content/mimiciii/get-zip/1.4/
    md5sum mimic-iii-clinical-database-1.4.zip
    # a3eb25060b7dc0843fe2235d81707552  mimic-iii-clinical-database-1.4.zip
    ```

4. Activate the Anaconda environment

    ``` bash
    conda env create -f dsp_emr_environment.yml
    source activate dsp_emr
    ```

5. Extract the ADMISSIONS and DIAGNOSES_ICD tables from the MIMIC-III zip file to the current directory.

    ``` bash
    python unpack_mimic.py -n data/ -v
    ```

6. Create dictionaries that map between Clinical Classifications Software (CCS) codes and ICD-9 codes diagnoses (`dxref2015.csv`) and procedures (`prref2015.csv`). The mapping data is derived from [here](https://www.hcup-us.ahrq.gov/toolssoftware/ccs/ccs.jsp)

    ``` bash
    python createCCSdict.py
    ```

7. Create training, testing, and validation sets of inputs to DoctorAI by reading in visit data, mapping diagnosis codes, partition the patients between sets, and for each set, printing out object files that contain patient ids (`_pids.*`), patient visit dates (`_dates.*`), diagnostic codes (`_seqs_visit.*`) and their labels (`_seqs_labels.*`) per patient visit

    ``` bash
    python process_mimic.py -a ADMISSIONS.csv -d DIAGNOSES_ICD.csv -o processed_data -v
    ```

8. Train DoctorAI model that take in 4894 diagnostic codes of one visit and predict 273 CCS codes for the next visit for 10 epochs. Use `python doctorAI.py -h` for more details about the default structure of the model.

    ``` bash
    python doctorAI.py processed_data_seqs_visit 4894 processed_data_seqs_label 273 \
        model_processed_data --verbose
    ```

9. Predict top 30 CCS codes for the subsequent visits for the patients in the test set

    ``` bash
    python testDoctorAI.py model_processed_data.9.npz \
        processed_data_seqs_visit.test processed_data_seqs_label.test \
        [200,200] --output_file predictions_processed_data.test --verbose
    ```

10. Convert prediction data object into two readable files of CCS codes, the top 30 predicted codes (`*.csv`) and the observed CCS codes that occurred (`*_actual.csv.`)

    ``` bash
    python translateCodesToText.py -c processed_data_label.types \
        -i predictions_processed_data.test.dat -o results_processed_data.test -v
    ```

## Extensions

The ways in which you could extend this include modifying this model to predict timing of events, predict a specific type of diagnosis only, or extend it to predict drug and procedure events in addition to diagnostics.  

