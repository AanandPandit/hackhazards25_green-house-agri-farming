
git clone git@github.com:AanandPandit/hackhazards25_green-house-agri-farming


Installing fluvio client:
sudo curl -fsS https://hub.infinyon.cloud/install/install.sh | bash
(restart the system after adding path)
fluvio cloud login
    InfinyOn Cloud email: 
    Password: 
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
in url
127.0.0.1:5000

now play with dashboard and see the changes in greenhouse simulator.