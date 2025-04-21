-----------------------------------------
| Greenhouse Agri-Farming Project Setup |
-----------------------------------------

Open the Terminal and follow the below instructions make sure that you are connected to internet:

1. Clone the Repository:
    git clone git@github.com:AanandPandit/hackhazards25_green-house-agri-farming
    cd hackhazards25_green-house-agri-farming

2. Install Fluvio Client:
    sudo curl -fsS https://hub.infinyon.cloud/install/install.sh | bash

    (After installing run this command to add path to system environment:)
    echo 'export PATH="${HOME}/.fvm/bin:${HOME}/.fluvio/bin:${PATH}"' >> ~/.zshrc
    sudo reboot
    (Reboot the system to take effect on changes of installation.)

3. Login to InfinyOn Cloud:
    fluvio cloud login
    (Enter your InfinyOn Cloud email and password when prompted.)

4. Create and Setup the Cluster:
    fluvio cloud cluster create greenhouse-agri       # Create cluster
    fluvio profile list                               # Check available clusters
    fluvio profile use greenhouse-agri                # Set cluster for use

5. Create Fluvio Topics:
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

6. Install Python Dependencies:
    sudo pip3 install -r requirements.txt --break-system-packages

7. Run the Project:

    Terminal 1: Start the Greenhouse Simulator:
        cd greenhouse
        python3 greenHouseSimulation.py

    Terminal 2: Start the Dashboard:
        cd webpage_dashboard
        python3 app.py

8. View the Dashboad:
    Open Firefox or any browser
    Got to http://localhost:5000

(Interact with the dashboard and watch real-time changes in the simulator.)

NOTE:
    More information at 'https://github.com/AanandPandit/hackhazards25_green-house-agri-farming'