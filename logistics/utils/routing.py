from collections import defaultdict, deque
import heapq
from ..models import Route, Location, Item, Shipment
from django.utils import timezone
from datetime import timedelta
import uuid

class RoutingEngine:
    """
    Implements routing algorithms for the logistics system.
    Uses Dijkstra's algorithm to find shortest paths between locations.
    """
    
    @staticmethod
    def build_graph():
        """
        Build a graph representation of the route network from the database.
        Returns a dictionary where keys are location IDs and values are 
        dictionaries of connected locations with travel costs.
        """
        graph = defaultdict(dict)
        # Only consider active routes
        active_routes = Route.objects.filter(active=True)
        
        for route in active_routes:
            # Add edge to graph with cost as weight
            graph[route.from_location.id][route.to_location.id] = {
                'cost': float(route.cost),
                'travel_time': route.travel_time,
                'route_id': route.id
            }
        
        return graph
    
    @staticmethod
    def dijkstra(graph, start_location_id, end_location_id):
        """
        Implements Dijkstra's algorithm to find the shortest path between two locations.
        Returns the path and total cost if a path is found, otherwise None.
        """
        # Initialize distances with infinity for all nodes except the start
        distances = {node: float('infinity') for node in graph}
        distances[start_location_id] = 0
        
        # Priority queue for Dijkstra
        pq = [(0, start_location_id)]
        
        # Predecessor dictionary to reconstruct path
        predecessors = {}
        
        # Route info to keep track of routes used
        route_info = {}
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            # If we've reached the destination, reconstruct and return the path
            if current_node == end_location_id:
                path = []
                node = end_location_id
                
                while node != start_location_id:
                    prev_node = predecessors[node]
                    path.append((prev_node, node, route_info[(prev_node, node)]))
                    node = prev_node
                    
                path.reverse()  # Reverse to get path from start to end
                return path, current_distance
            
            # If we've already found a better path to this node, skip
            if current_distance > distances[current_node]:
                continue
            
            # Check all neighbors of current node
            for neighbor, edge_data in graph[current_node].items():
                distance = current_distance + edge_data['cost']
                
                # If we found a better path to the neighbor
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    predecessors[neighbor] = current_node
                    route_info[(current_node, neighbor)] = edge_data
                    heapq.heappush(pq, (distance, neighbor))
        
        # If we get here, no path was found
        return None, float('infinity')
    
    @staticmethod
    def find_optimal_route(from_location_id, to_location_id):
        """
        Find the optimal route between two locations.
        Returns a list of route segments (location pairs) and the total cost.
        """
        graph = RoutingEngine.build_graph()
        path, total_cost = RoutingEngine.dijkstra(graph, from_location_id, to_location_id)
        
        if path is None:
            return None, float('infinity')
        
        # Convert location IDs to actual Location objects and include route details
        route_segments = []
        for from_id, to_id, edge_data in path:
            from_location = Location.objects.get(id=from_id)
            to_location = Location.objects.get(id=to_id)
            route = Route.objects.get(id=edge_data['route_id'])
            
            route_segments.append({
                'from_location': from_location,
                'to_location': to_location,
                'cost': edge_data['cost'],
                'travel_time': edge_data['travel_time'],
                'route': route
            })
        
        return route_segments, total_cost
    
    @staticmethod
    def create_shipments_for_items(items, destination_location_id):
        """
        Create optimal shipments for a list of items to reach the destination.
        Groups items by current location and plans routes.
        """
        # Group items by current location
        items_by_location = defaultdict(list)
        items_without_location = []
        
        for item in items:
            if item.current_location:
                items_by_location[item.current_location.id].append(item)
            else:
                # Collect items with no location for special handling
                items_without_location.append(item)
        
        created_shipments = []
        
        # For each location with items
        for location_id, location_items in items_by_location.items():
            if location_id == destination_location_id:
                # Items are already at destination, no shipment needed
                continue
            
            # Find optimal route from current location to destination
            route_segments, total_cost = RoutingEngine.find_optimal_route(location_id, destination_location_id)
            
            if not route_segments:
                # No route found, create direct shipment if possible
                try:
                    from_location = Location.objects.get(id=location_id)
                    to_location = Location.objects.get(id=destination_location_id)
                    
                    # Create a direct shipment
                    departure_time = timezone.now() + timedelta(hours=1)
                    arrival_time = departure_time + timedelta(hours=2)  # Default 2 hour travel time
                    
                    shipment = Shipment.objects.create(
                        shipment_number=f"SH-{uuid.uuid4().hex[:8].upper()}",
                        from_location=from_location,
                        to_location=to_location,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        vehicle_info=f"Auto-assigned Vehicle (Direct)"
                    )
                    
                    # Add items to shipment and update their status
                    for item in location_items:
                        shipment.items.add(item)
                        item.update_status('in_transit', from_location)
                    
                    created_shipments.append(shipment)
                except Exception as e:
                    # Log exception or handle error
                    continue
            else:
                # Create shipments for each segment of the route
                current_items = location_items
                from_location = Location.objects.get(id=location_id)
                
                for segment in route_segments:
                    # Create a shipment for this segment
                    departure_time = timezone.now() + timedelta(hours=1)  # Schedule for 1 hour later
                    arrival_time = departure_time + segment['travel_time']
                    
                    shipment = Shipment.objects.create(
                        shipment_number=f"SH-{uuid.uuid4().hex[:8].upper()}",
                        from_location=segment['from_location'],
                        to_location=segment['to_location'],
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        vehicle_info=f"Auto-assigned Vehicle"
                    )
                    
                    # Add items to shipment and update their status
                    for item in current_items:
                        shipment.items.add(item)
                        item.update_status('in_transit', segment['from_location'])
                    
                    created_shipments.append(shipment)
                    
                    # Next shipment will start from where this one ends
                    from_location = segment['to_location']
        
        # Handle items without location - create direct shipments from a default warehouse
        if items_without_location:
            try:
                # Try to find a warehouse to use as origin
                default_warehouse = Location.objects.filter(location_type='warehouse').first()
                destination_location = Location.objects.get(id=destination_location_id)
                
                if default_warehouse:
                    # Create a shipment from default warehouse to destination
                    departure_time = timezone.now() + timedelta(hours=1)
                    arrival_time = departure_time + timedelta(hours=2)  # Default 2 hour travel time
                    
                    shipment = Shipment.objects.create(
                        shipment_number=f"SH-{uuid.uuid4().hex[:8].upper()}",
                        from_location=default_warehouse,
                        to_location=destination_location,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        vehicle_info=f"Auto-assigned Vehicle (For new items)"
                    )
                    
                    # Add items to shipment and update their status
                    for item in items_without_location:
                        shipment.items.add(item)
                        item.update_status('in_transit', default_warehouse)
                    
                    created_shipments.append(shipment)
            except Exception as e:
                # Log exception or handle error
                pass
        
        return created_shipments