import heapq

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def insert(self, item, priority, arrival_to_item, path_via):
        # print('from pq', item)
        heapq.heappush(self._queue, (priority, self._index, arrival_to_item, path_via, item))
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

    def change_priority_with_if(self, item, new_priority, path_via, new_arrival):
        for i, n in enumerate(self._queue):
            if n[-1] == item:
                # If stored cost is larger than new
                if (n[2] > new_arrival):
                    print(item, 'rn it takes', n[0], 'via', n[-2], 'and arrives at', n[2], 'but via', path_via, 'it takes', new_priority, 'and arrives', new_arrival)
                    self._queue[i] = (new_priority, n[1], new_arrival, path_via, n[-1])
                    # self._queue[i] = (new_priority, *n[1:])
                    heapq.heapify(self._queue)
                return
        # print('No such item found')
        return -1

    def count(self):
        return len(self._queue)


if __name__ == '__main__':
    pq = PriorityQueue()

    pq.insert(11, 5, 12)
    pq.insert(10, 2, 13)

    print(pq.get_lowest())
    pq.change_priority(11, 1)

    # ! ( priority, index, path_via, item/id )

    print(pq.extract_lowest())
    print(pq.get_lowest())