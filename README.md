# Amp_controller
Controller for a Programmable System on a Chip (PSoC) electrochemical device


Future directions:
- add extra threads to poll endpoints
- add data points during cyclic voltammerty run if it is slower than 500 ms
- also add a progress bar and timer for CV
- if data read fails, check status of PSoC- needs firmware update also
- add more electrochemical techniques such as: SWV, NPV, ptoetiometry.  needs firmware update also
  - make a parent frame and data for these that is better then the current CV class and frame
