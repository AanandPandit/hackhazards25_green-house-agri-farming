
git clone git@github.com:AanandPandit/hackhazards25_green-house-agri-farming


Installing fluvio client:
sudo curl -fsS https://hub.infinyon.cloud/install/install.sh | bash
(reboot the system after adding path)

fluvio cloud login
    InfinyOn Cloud email: 
    Password:

to create cluster:
    fluvio cloud cluster create greenhouse-agri

to check the list of cluster:
    fluvio profile list

to choose the cluster to use:
    fluvio profile use greenhouse-agri

------------------------------------------------------
fluvio topic create 
---------------------------
fluvio topic create dht-temp
fluvio topic create dht-humid
fluvio topic create co2
fluvio topic create rain-sensor
fluvio topic create soil-moisture-1
fluvio topic create soil-moisture-2
fluvio topic create water-level-sensor
fluvio topic create fan-1
fluvio topic create fan-2
fluvio topic create fan-3
fluvio topic create fan-4
fluvio topic create fan-5
fluvio topic create ac-1
fluvio topic create ac-2
fluvio topic create humidifier-1
fluvio topic create humidifier-2
fluvio topic create humidifier-3
fluvio topic create light-1
fluvio topic create light-2
fluvio topic create light-3
fluvio topic create light-4
fluvio topic create light-5
fluvio topic create water-pump
---------------------------------------------------------------

sudo pip3 install -r requirements.txt --break-system-packages

Here are two files to run for this project
1. First is greenhouse simulator
2. second is webdashboard

go to greenhouse> 
python3 greenHouseSimulation.py 

open another bash/shell
go to webpage_dashboard>
python3 app.py 

open firefox browser>
in url box
localhost:5000

now play with dashboard and see the changes in greenhouse simulator.