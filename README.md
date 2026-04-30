# AmbiLog

**AmbiLog** is a software developed in collaboration with researcher Marcelo de Cicco from Inmetro. This tool focuses on the sensing and storage of environmental variables such as temperature (TCA and TCB) and relative humidity (RHA and RHB) in Inmetro's Interferometry Laboratory. 

The laboratory environmental variables are continuously monitored in a graphical interface with a sliding window style. Environmental data are stored in XML files with structured nodes for each measurement. Each MJD has its own XML data file, and each node in the XML file contains a timestamp for the respective node measurements. Data are collected almost simultaneously for both internal and external variables. The XML nodes are initially stored in stream mode in the computer's memory and, after a certain (programmable) number of measurements; the software saves the XML file with a naming convention that allows identification of the saved data.
 
It is also important to note:
1. The software is portable so it can be used both from a pen drive as from a web server;
2. The software is cross platform and so it works on both Windows and Linux;
3. The software can communicate with and configure a Data logger **KeySight 34970A** equipment via VISA interface.
