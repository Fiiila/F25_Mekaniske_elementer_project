# F25_Mekaniske_elementer_project
This repository is containing files required for running UI application for exercise machine from course 
Mekaniske elemeneter at SDU during Spring semester 2025. Hardware and further sensor information 
are located in handed in report.

## Repository description
There are located several files for running application.

- `data_read.ino` - acquire data from sensors using arduino and transferring via serial connection.
- `read_serial.py` - class reading from serial link (USB) connection 
made for multiprocessing runtime in python returning array of values
- `pull_machine_app.py` - main python **UI application to be run** visualizing result

## How to make it run?
To be able to run this application, certain libraries has to be installed in your python installation.
This can be done by executing following command in root directory of this repository.

```python
    pip install -r requirements.txt
```