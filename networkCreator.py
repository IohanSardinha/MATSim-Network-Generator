from osmhandlers import GetPublicTransportMembersHandler, NetworkBuilder
from gtfsprocessor import GTFSHandler

def main(OSM_FILE, GTFS_FILE, OUTPUT_NETWORK_FILE, OUTPUT_TRANSIT_SCHEDULE_FILE):
    publicTransportMembersHandler = GetPublicTransportMembersHandler()
    print('Processing public transport network from osm...')
    publicTransportMembersHandler.apply_file(OSM_FILE)
    print('Done')

    networkBuilder = NetworkBuilder(publicTransportMembersHandler.publicTransportMembers)
    print('Building MATSim network from osm...')
    networkBuilder.apply_file(OSM_FILE)
    print('Done')

    gtfsHandler = GTFSHandler(GTFS_FILE)
    print('Processing GTFS file...')
    gtfsHandler.processGTFS()
    print('Done')

    print(str(gtfsHandler))

    with open(OUTPUT_NETWORK_FILE, 'w') as file:
        print('Writing network to file...')
        file.write(str(networkBuilder))
        print('Done')

if __name__ == '__main__':
    main('porto.osm','gtfs_mdp_11_09_2023.zip', 'network.xml', 'transitSchedule.xml')