from helper import *
import gtfs_kit as gk
from xml.dom import minidom 
from haversine import haversine, Unit
import numpy as np

class GTFSHandler:
    def __init__(self, feedFileName, links, relations, wayLinks, units='km'):
        self.feed = gk.read_feed(feedFileName, dist_units=units)
        self.links = links
        self.realtions = relations
        self.wayLinks = wayLinks
        self.stop_links = {}
        self.vehicles = []

    def __str__(self):
        return self.xmlRoot.toprettyxml(indent="\t")
    
    def createRouteRelations(self):
        self.agency_relations = {}
        for rID, relation in self.realtions.items():
            tags = relation['tags']
            if  get(tags, 'operator') == self.agency_name\
             or get(tags, 'operator:wikipedia') == self.agency_name\
             or get(tags, 'operator') == f"pt:{self.agency_name}"\
             or get(tags, 'operator:wikipedia') == f"pt:{self.agency_name}"\
             or get(tags, 'network') == self.agency_name\
             or get(tags, 'operator') == self.agency_id\
             or get(tags, 'operator:wikipedia') == self.agency_id\
             or get(tags, 'operator') == f"pt:{self.agency_id}"\
             or get(tags, 'operator:wikipedia') == f"pt:{self.agency_id}"\
             or get(tags, 'network') == self.agency_id:
                pathMembers = [id for id in relation['members'] if id in self.wayLinks]
                route_f = []
                route_r = []
                size = len(pathMembers)
                for i in range(size):
                    route_f += self.wayLinks[pathMembers[i]]['f']
                    route_r += self.wayLinks[pathMembers[size-i-1]]['r'][::-1]
                self.agency_relations[get(tags, 'ref')] = {'f':route_f,'r':route_r}
    
    def createProfiles(self):
        profiles = {r['route_id']:{} for _,r in self.feed.routes.iterrows()}

        for trip_id in self.stop_times['trip_id'].unique():
            trip = self.stop_times[self.stop_times['trip_id'] == trip_id].sort_values(by='stop_sequence')
            profile = [(trip.iloc[0]['stop_id'], '00:00:00', (trip.iloc[0]["stop_lat"], trip.iloc[0]["stop_lon"]), trip.iloc[0]["stop_name"])]
            for i in range(1,len(trip)):
                diff = (parse_time(trip.iloc[i]['arrival_time']) - parse_time(trip.iloc[i-1]['arrival_time'])) + parse_time(profile[i-1][1])
                profile.append((trip.iloc[i]['stop_id'], str(diff), (trip.iloc[i]["stop_lat"], trip.iloc[i]["stop_lon"]), trip.iloc[i]["stop_name"] ))
            profileID = '>'.join([f'{s}::{t}' for s, t,_,_ in profile])
            if not profileID in profiles[trip.iloc[0]['route_id']]:
                profiles[trip.iloc[0]['route_id']][profileID] = {'profile':profile,'trips':[trip_id]}
            else:
                profiles[trip.iloc[0]['route_id']][profileID]['trips'].append(trip_id)
        
        self.profiles = profiles
    
    def setupXML(self):
        imp = minidom.getDOMImplementation()
        doctype = imp.createDocumentType("transitSchedule", None, "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd")
        root = imp.createDocument(None, "transitSchedule", doctype)
        self.xmlRoot = root

        attributes = self.xmlRoot.createElement("attributes")

        #CHECK THIS DATES IN THE FUTURE
        createElement(self.xmlRoot, "attribute", '2024-01-08', attributes, name="endDate", __class="java.lang.String")
        createElement(self.xmlRoot, "attribute", '2024-01-08', attributes, name="startDate", __class="java.lang.String")

        self.xmlRoot.documentElement.appendChild(attributes)

        self.transitStops = createElement(self.xmlRoot, "transitStops", __parent__= self.xmlRoot.documentElement)

    def createStops(self):
        
        #CREATE STOPS AS THEY ARE ADDED TO ROUTE ROUTE

        transitStops = self.xmlRoot.createElement('transitStops')

        links = []
        for route in self.agency_relations.values():
            links += route['f']
            links += route['r']
        
        self.xmlRoot.documentElement.appendChild(transitStops)
        for _,  stopRow in self.feed.stops.iterrows():
            closest = None
            dist = 999999
            for id in links:
                link = self.links[id]
                
                tmpDist = min(haversine((stopRow['stop_lat'], stopRow['stop_lon']), link['from']), haversine((stopRow['stop_lat'], stopRow['stop_lon']), link['to']))
                if tmpDist < dist:
                    dist = tmpDist
                    closest = id
            
            if(dist > 1):
                closest = 'null'
                #continue

            self.stop_links[stopRow['stop_id']] = closest 
            createElement(self.xmlRoot, 'stopFacility', __parent__=transitStops, id=stopRow['stop_id'], x=stopRow['stop_lon'], y=stopRow['stop_lat'], linkRefId=closest ,name=stopRow['stop_name'], isBlocking='false')

    def createTransitRoutes(self, route_id, route_profile, transitLine):
        route_name = self.feed.routes[self.feed.routes['route_id'] == route_id].iloc[0]['route_short_name']
        for i, (_, profileDesc) in enumerate(route_profile.items()):
            profile = profileDesc['profile']
            departureTrips = profileDesc['trips']
            
            transitRoute = createElement(self.xmlRoot, "transitRoute", __parent__=transitLine, id=f"{self.agency_id}-{route_id}-{i}")
            createElement(self.xmlRoot, "transportMode", self.transportMode, transitRoute)
            routeProfile = createElement(self.xmlRoot, "routeProfile", __parent__=transitRoute)
            routeXml = createElement(self.xmlRoot, 'route', __parent__=transitRoute)
            departures = createElement(self.xmlRoot, "departures", __parent__=transitRoute)

            firstStopIndex = -1
            route = None
            for i, (_, _, location, _) in enumerate(profile):
                for linkId in self.agency_relations[route_name]['f']:
                    dist = min(haversine(location, self.links[linkId]['from']), haversine(location, self.links[linkId]['to']))
                    if dist <= 0.5:
                        route = self.agency_relations[route_name]['f']
                        break
                for linkId in self.agency_relations[route_name]['r']:
                    dist = min(haversine(location, self.links[linkId]['from']), haversine(location, self.links[linkId]['to']))
                    if dist < 1:
                        route = self.agency_relations[route_name]['r']
                        break
                if route != None:
                    firstStopIndex = i
                    break
            
            last_link = 0
            for i in range(firstStopIndex, len(profile)):
                stop, time, location, name = profile[i]
                dist = 999999
                closest = None
                for j in range(last_link, len(route)):
                    link = self.links[route[j]]

                    tmpDist = min(haversine(location, link['from']), haversine(location, link['to']))
                    if tmpDist < dist:
                        dist = tmpDist
                        closest = route[j]
                        last_link = j

                createElement(self.xmlRoot, 'stop', __parent__=routeProfile, refId=stop, arrivalOffset=time, departureOffset=time, awaitDeparture='true')
                createElement(self.xmlRoot, 'stopFacility', __parent__=self.transitStops, id=stop, x=location[1], y=location[0], linkRefId=closest ,name=name, isBlocking='false')

            for trip in departureTrips:
                departureTime=self.stop_times[self.stop_times['trip_id'] == trip]['arrival_time'].min()
                createElement(self.xmlRoot, 'departure', __parent__=departures, id=trip, departureTime=fix_time(departureTime), vehicleRefId=f'{self.agency_id}_{trip}')
                self.vehicles.append(f'{self.agency_id}_{trip}')
            
            
            for linkId in route:
                createElement(self.xmlRoot, 'link', __parent__=routeXml, refId=linkId)
            
            
            break        

    def createTransitLines(self):
        for route_id, route_profile in self.profiles.items():
            route_type = self.feed.routes[self.feed.routes["route_id"] == route_id].iloc[0]["route_type"]

            transitLine = createElement(self.xmlRoot, "transitLine",  __parent__=self.xmlRoot.documentElement, id=f"{self.agency_id}-{route_id}") 
            attributes = createElement(self.xmlRoot, "attributes", __parent__=transitLine)
            createElement(self.xmlRoot, "attribute", self.agency_id, attributes, name="gtfs_agency_id", __class="java.lang.String")
            createElement(self.xmlRoot, "attribute", route_id, attributes, name="gtfs_route_short_name", __class="java.lang.String")
            createElement(self.xmlRoot, "attribute", str(route_type), attributes, name="gtfs_route_type", __class="java.lang.String")

            self.createTransitRoutes(route_id, route_profile, transitLine)
            break
            

    def processGTFS(self):
        self.agency_name = self.feed.agency.iloc[0]['agency_name']
        self.agency_id = self.agency_name.replace(' ','_') if self.feed.agency['agency_id'].isna()[0] else self.feed.agency['agency_id'][0]

        self.transportMode = "bus"

        self.stop_times = self.feed.stop_times.merge(self.feed.trips, left_on="trip_id", right_on="trip_id")\
                                         .merge(self.feed.stops, left_on="stop_id", right_on="stop_id")\
                                         .merge(self.feed.calendar, left_on='service_id', right_on='service_id')\
                                         .merge(self.feed.routes, left_on='route_id', right_on='route_id')\
                                         .sort_values(by=['trip_id','route_id', 'arrival_time'])
        
        self.stop_times = self.stop_times[self.stop_times['monday'] == 1]

        print('creating profiles')
        self.createProfiles()
        print('creating relation')
        self.createRouteRelations()
        print('setting up xml')
        self.setupXML()
        print('creating lines')
        self.createTransitLines()
