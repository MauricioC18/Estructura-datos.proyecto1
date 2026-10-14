class EventQueue:

    def __init__(self):
        self._heap = []

    def __len__(self):
        return len(self._heap)

    def is_empty(self):
        self._discard_cancelled_roots()
        return len(self._heap) == 0

    def _less(self, first, second):
        if first.time != second.time:
            return first.time < second.time

        return first.sequence < second.sequence

    def push(self, event):
        self._heap.append(event)
        self._sift_up(len(self._heap) - 1)

    def peek(self):
        self._discard_cancelled_roots()

        if not self._heap:
            return None

        return self._heap[0]

    def pop(self):
        self._discard_cancelled_roots()

        if not self._heap:
            return None

        return self._remove_root()

    def cancel(self, event):
        event.cancelled = True

    def active_events(self):
        """Eventos no cancelados, para guardar la agenda en disco.

        No los devuelve en orden de prioridad. Al cargarlos basta con volver a
        insertarlos: cada evento conserva su tiempo y su numero de secuencia,
        de modo que el monticulo reconstruye el mismo orden.
        """
        return [event for event in self._heap if not event.cancelled]

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2

            if not self._less(
                self._heap[index],
                self._heap[parent]
            ):
                break

            self._heap[index], self._heap[parent] = (
                self._heap[parent],
                self._heap[index]
            )

            index = parent

    def _sift_down(self, index):
        size = len(self._heap)

        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            if (
                left < size
                and self._less(
                    self._heap[left],
                    self._heap[smallest]
                )
            ):
                smallest = left

            if (
                right < size
                and self._less(
                    self._heap[right],
                    self._heap[smallest]
                )
            ):
                smallest = right

            if smallest == index:
                break

            self._heap[index], self._heap[smallest] = (
                self._heap[smallest],
                self._heap[index]
            )

            index = smallest

    def _remove_root(self):
        root = self._heap[0]
        last = self._heap.pop()

        if self._heap:
            self._heap[0] = last
            self._sift_down(0)

        return root

    def _discard_cancelled_roots(self):
        while self._heap and self._heap[0].cancelled:
            self._remove_root()
