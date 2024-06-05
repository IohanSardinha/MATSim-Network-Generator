import osmium
from xml.dom import minidom 
from haversine import haversine, Unit
import helper
from pyreproj import Reprojector


class GetPublicTransportMembersHandler(osmium.SimpleHandler):
    def __init__(self):
        super(GetPublicTransportMembersHandler, self).__init__()
        self.publicTransportMembers = {}
        self.relations = {}

    def relation(self, r):
        if r.tags.get("public_transport:version") == '2' and r.tags.get("type") == "route":
            self.relations[r.id] = {'tags': {t.k:t.v for t in r.tags}, 'members':[m.ref for m in r.members if m.type == 'w']}
            for member in r.members:
                self.publicTransportMembers[member.ref] = {t.k:t.v for t in r.tags}
                self.publicTransportMembers[member.ref]['relation_id'] = r.id

class NetworkBuilder(osmium.SimpleHandler):
    def __init__(self, ptMembers):
        super(NetworkBuilder, self).__init__()
        self.ptMembers = ptMembers
        self.setupNetwork()
        self.nodesLocations = {}
        self.createdNodes = set()
        self.ptLinks = {}
        self.wayLinks = {}
        reprojector = Reprojector()
        self.coordinateTransformer = reprojector.get_transformation_function(from_srs="WGS84", to_srs="EPSG:3857")

    def setupNetwork(self):
        imp = minidom.getDOMImplementation()
        doctype = imp.createDocumentType("network", None, "http://www.matsim.org/files/dtd/network_v2.dtd")
        root = imp.createDocument(None, "network", doctype)
        self.xmlRoot = root

        self.nodes = self.xmlRoot.createElement("nodes")

        self.xmlRoot.documentElement.appendChild(self.nodes)

        self.links = self.xmlRoot.createElement("links")

        self.xmlRoot.documentElement.appendChild(self.links)

    def createLink(self, id, _from, to, modes, freespeed, capacity ,lanes, pt=False):
       
        if not _from.ref in self.createdNodes:
            x,y = self.coordinateTransformer(self.nodesLocations[_from.ref][0], self.nodesLocations[_from.ref][1])
            self.createNode(_from, x, y)

        if not to.ref in self.createdNodes:
            x, y = self.coordinateTransformer(self.nodesLocations[to.ref][0], self.nodesLocations[to.ref][1])
            self.createNode(to, x, y)

        if pt:
            self.ptLinks[id] = {'from':self.nodesLocations[_from.ref], 'to':self.nodesLocations[to.ref]}
            
        xmlLink = self.xmlRoot.createElement("link")
        xmlLink.setAttribute("id", str(id))
        xmlLink.setAttribute("from", str(_from))
        xmlLink.setAttribute("to", str(to))
        xmlLink.setAttribute('length', str(haversine(self.nodesLocations[_from.ref], self.nodesLocations[to.ref], Unit.METERS)))
        xmlLink.setAttribute('freespeed', str(freespeed))
        xmlLink.setAttribute('capacity', str(lanes*capacity))
        xmlLink.setAttribute('permlanes', str(lanes))
        xmlLink.setAttribute('oneway', '1')
        xmlLink.setAttribute("modes", modes)
        self.links.appendChild(xmlLink)

    def createNode(self, id, x, y):
        xmlNode = self.xmlRoot.createElement("node")
        xmlNode.setAttribute("id", str(id))
        xmlNode.setAttribute("x", str(x))
        xmlNode.setAttribute("y", str(y))
        self.nodes.appendChild(xmlNode)
        self.createdNodes.add(id.ref)

    def __str__(self):
        return self.xmlRoot.toprettyxml(indent="\t")

    def node(self, n):
        #self.createNode(n.id, n.location.lon, n.location.lat)
        self.nodesLocations[n.id] = (n.location.lat, n.location.lon)

    def way(self, w):
        highway_types = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "minor", "unclassified", "residential", "service", "living_street"]
        self.wayLinks[w.id] = {'f':[], 'r':[]}
        if w.tags.get("highway") in highway_types:
            for i in range(len(w.nodes)-1):
                modes = "car"
                pt = False
                if w.id in self.ptMembers:
                    modes += f",{self.ptMembers[w.id]['route']}"
                    pt = True

                created = False
                if helper.forward(w) or not helper.backwards(w):
                    self.wayLinks[w.id]['f'].append(f"{w.id}{i}")
                    self.createLink(f"{w.id}{i}", w.nodes[i], w.nodes[i+1], modes, helper.getfreeSpeed(w), helper.getCapacity(w), helper.getNLanes(w), pt)
                    created = True
                    
                if helper.backwards(w):
                    self.wayLinks[w.id]['r'].append(f"{w.id}{i}_r")
                    self.createLink(f"{w.id}{i}_r", w.nodes[i+1], w.nodes[i], modes, helper.getfreeSpeed(w), helper.getCapacity(w), helper.getNLanes(w), pt)
                    created = True
                
                if not created:
                    print(w.id)

        railway_types = ["funicular", "light_rail","miniature", "monorail", "narrow_gauge", "rail", "subway", "tram"]
        if w.tags.get("railway") in railway_types and w.id in self.ptMembers:
            for i in range(len(w.nodes)-1):
                
                
                self.wayLinks[w.id]['f'].append(f"{w.id}{i}")
                self.createLink(f"{w.id}{i}", w.nodes[i], w.nodes[i+1], w.tags.get("railway"), helper.getfreeSpeed(w), helper.getCapacity(w), helper.getNLanes(w), True)
            
                self.wayLinks[w.id]['r'].append(f"{w.id}{i}_r")
                self.createLink(f"{w.id}{i}_r", w.nodes[i+1], w.nodes[i], w.tags.get("railway"), helper.getfreeSpeed(w), helper.getCapacity(w), helper.getNLanes(w), True)
                

                