from networkCreator import main as createNetwork

OSM_FILE = 'porto.osm'
GTFS_FILE = 'gtfs_mdp_11_09_2023.zip'
OUTPUT_NETWORK_FILE = 'network.xml'
OUTPUT_TRANSIT_SCHEDULE_FILE = 'transitSchedule.xml'

createNetwork(OSM_FILE, GTFS_FILE, OUTPUT_NETWORK_FILE, OUTPUT_TRANSIT_SCHEDULE_FILE)