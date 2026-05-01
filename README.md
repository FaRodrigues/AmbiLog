Install and Run Dependencies

If you have just downloaded the project and it fails due to missing modules, you may need to install its requirements first:
Install dependencies: python -m pip install -r requirements.txt.
Run the script: python main.py

# AmbiLog

**AmbiLog** is a software developed in collaboration with Inmetro researcher Marcelo de Cicco. This tool focuses on the detection and storage of environmental variables such as temperature (TCA and TCB) and relative humidity (RHA and RHB) at the Inmetro Interferometry Laboratory (Laint), which is the laboratory responsible for UTC (INXE).

The environmental variables of the laboratory are continuously monitored in a graphical interface with a sliding window style. Environmental data is stored in XML files with structured nodes for each measurement. Each MJD has its own XML data file named with the YYDOY naming convention, and each node in the XML file contains a date and timestamp for the respective node measurements (see varamblog folder).

Data are collected almost simultaneously for both internal and external variables. The XML nodes are initially stored in stream mode in the computer's memory and, after a certain (programmable) number of measurements; the software saves the XML file with a naming convention that allows identification of the saved data.
 
It is also important to note:
1. The software is portable so it can be used both from a pen drive as from a web server;
2. The software is cross platform and so it works on both Windows and Linux;
3. The software can configure a Data logger **KeySight 34970A** equipment and communicate with it using VISA interface.

4. Example of a measurement node from the ***/varamblog/26119/log_ambientvars-26119.xml*** file:

           <measure timestamp="2026-04-29 00:00:59.731909">
            <RHA>80.20</RHA>
            <SIGMA_RHA>1.11</SIGMA_RHA>
            <TCA>20.42</TCA>
            <SIGMA_TCA>0.20</SIGMA_TCA>
            <RHB>44.28</RHB>
            <SIGMA_RHB>1.11</SIGMA_RHB>
            <TCB>22.84</TCB>
            <SIGMA_TCB>0.20</SIGMA_TCB>
           </measure>
