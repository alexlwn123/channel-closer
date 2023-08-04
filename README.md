# Channel Closer Script

* Prompts user for LND connection information (rest)
* Creates a list of channels that have not been used in the past 2 weeks
* Closes each "cold" channel


## Running

* Install python3   
  * MacOS: `brew install python3`  
* Clone, install, and run
```zsh
 git clone git@github.com:alexlwn123/channel-closer.git 
 cd channel-closer
 python3 -m pip install -r requirements.txt
 python3 main.py
```