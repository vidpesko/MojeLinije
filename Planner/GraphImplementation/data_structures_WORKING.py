import heapq

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def insert(self, item, cost_to_node, arrival_to_item, departure_from_start, path_via, route_id, shape_lookup):
        # print('from pq', item)
        heapq.heappush(self._queue, (arrival_to_item, self._index, cost_to_node, route_id, departure_from_start, shape_lookup, path_via, item))
        self._index += 1

    def extract_lowest(self):
        return heapq.heappop(self._queue)
        # print('REMOVING', o[-1])

    def get_lowest(self):
        return self._queue[0]

    def change_priority(self, item, new_priority):
        for i, n in enumerate(self._queue):
            if n[-1] == item:
                self._queue[i] = (new_priority, *n[1:])
                heapq.heapify(self._queue)
                return
        print('No such item found')

    # ! OPTIMISATION WELCOME!

    def change_priority_with_if(self, item, new_priority, new_dep_from_a, new_path_via, new_cost, new_route_via, new_shape_lookup, absolute_start_id):
        for i, n in enumerate(self._queue):
            if n[-1] == item:
                # If stored cost is larger than change
                if n[0] > new_priority:
                    self._queue[i] = (new_priority, n[1], new_cost, new_route_via, new_dep_from_a, new_shape_lookup, new_path_via, n[-1])
                    heapq.heapify(self._queue)
                return
        # print('No such item found')
        return -1

    def count(self):
        return len(self._queue)
    
    def change_start_node_lookup(self, new_lookup, _visited):
        current_node = _visited[0]
        _visited[0] = (*current_node[0:5], new_lookup, *current_node[-2:])
        return _visited


# class AdditionalData:


if __name__ == '__main__':
    pq = PriorityQueue()

    pq.insert(11, 5, 12)
    pq.insert(10, 2, 13)

    print(pq.get_lowest())
    pq.change_priority(11, 1)

    # ! ( priority, index, path_via, item/id )

    print(pq.extract_lowest())
    print(pq.get_lowest())