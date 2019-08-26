# import the necessary packages
from scipy.spatial import distance as dist
import numpy as np
import logging
from typing import List, Dict, Tuple, Set
from Library.DatabaseHandler import Person

def centroid(rect) -> Tuple:
    """Calculate the centroid point of a face bounding box

    Arguments:
        rect -- The bounding box of the face

    Returns:
        Tuple -- The centroid point
    """
    (startY, endX, endY, startX) = rect
    cX = int((startX + endX) / 2.0)
    cY = int((startY + endY) / 2.0)
    return (cX, cY)

class TrackedPerson():
    person: Person
    rect: Tuple
    centroid: Tuple
    disappearCount: int = 0
    maxDisappeared: int
    tracker: 'CentroidTracker'

    def __init__(self, person: Person, rect: Tuple, tracker: 'CentroidTracker', maxDisappeared: int = 50):
        self.person = person
        self.rect = rect
        self.centroid = centroid(rect)
        self.maxDisappeared = maxDisappeared
        self.tracker = tracker

    def disappear(self):
        self.disappearCount += 1
        if self.disappearCount > self.maxDisappeared:
            self.tracker.deregister(self)

    def appear(self, rect, cent=None):
        self.disappearCount = 0
        self.rect = rect
        self.centroid = cent or centroid(rect)
        self.tracker.seen.add(self)

class CentroidTracker():
    objects: Set[TrackedPerson]

    def __init__(self, maxDisappeared=50):
        # initialize the next unique object ID along with two ordered
        # dictionaries used to keep track of mapping a given object
        # ID to its bounding box and number of consecutive frames it has
        # been marked as "disappeared", respectively
        self.objects = set()
        self.seen = set()
        self.prev_ids = list()

        # store the number of maximum consecutive frames a given
        # object is allowed to be marked as "disappeared" until we
        # need to deregister the object from tracking
        self.maxDisappeared = maxDisappeared

    def register(self, tracked: TrackedPerson):
        """Register a new person in the tracking registry

        Arguments:
            tracked {TrackedPerson} -- The person the face was associated with
        """
        self.objects.add(tracked)

    def deregister(self, tracked: TrackedPerson) -> bool:
        """Deregister tracked person from the tracking registry

        Arguments:
            tracked {TrackedPerson} -- The person to deregister

        Returns:
            bool -- True if the person was in the registry
        """
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        try:
            self.objects.remove(tracked)
            return True
        except KeyError:
            return False

    def rebase(self, person_to_face_rect_dict: Dict[Person, Tuple]) -> Set[TrackedPerson]:
        """Rebase the whole registry based on a new DNN run

        Arguments:
            person_to_face_rect_dict {Dict[Person, Tuple]} -- [description]
        """
        for (person, rect) in person_to_face_rect_dict.items():
            tracker = self.tracker_by_person(person)
            if tracker is None:
                self.register(TrackedPerson(person, rect, self, self.maxDisappeared))
            else:
                tracker.appear(rect)
        return self.objects

    def tracker_by_person(self, person: Person):
        for tracked in self.objects:
            if tracked.person == person:
                return tracked
        return None

    def update(self, rects) -> Set[TrackedPerson]:
        """Attempt to pair the face bounding boxes from the current frame with the centroids in the registry
        and update the registry accordingly. People that disappear for too many frames are removed from the registry.

        Arguments:
            rects -- Face bounding rectangles in (top, right, bottom, left) order

        Returns:
            List -- List of tuples of face bounding boxes and their respective person
        """
        # clear the objects seen in the current frame
        self.seen.clear()

        # check to see if the list of input bounding box rectangles
        # is empty
        if len(rects) == 0:
            # loop over any existing tracked objects and mark them
            # as disappeared
            for tracked in list(self.objects):
                tracked.disappear()

            # return early as there are no centroids or tracking info
            # to update
            return self.objects
        # initialize an array of input centroids for the current frame
        inputCentroids = np.zeros((len(rects), 2), dtype="int")

        # loop over the bounding box rectangles
        for (i, rect) in enumerate(rects):
            # use the bounding box coordinates to derive the centroid
            inputCentroids[i] = centroid(rect)

        # if we are currently not tracking any objects but there are faces on the frame
        # we can't really do anything so we'll just return an empty dictionary

        # create a list from our objects to define an order on them
        objects = list(self.objects)
        objects: List[TrackedPerson]

        # create a list of their centroids with the same order
        objectCentroids = [tracked.centroid for tracked in self.objects]

        try:
            if len(self.objects) == 0:
                return self.objects

            # otherwise, we are currently tracking objects so we need to
            # try to match the input centroids to existing object
            # centroids
            else:
                # compute the distance between each pair of object
                # centroids and input centroids, respectively -- our
                # goal will be to match an input centroid to an existing
                # object centroid
                D = dist.cdist(np.array(objectCentroids), inputCentroids)

                # in order to perform this matching we must (1) find the
                # smallest value in each row and then (2) sort the row
                # indexes based on their minimum values so that the row
                # with the smallest value is at the *front* of the index
                # list
                rows = D.min(axis=1).argsort()

                # next, we perform a similar process on the columns by
                # finding the smallest value in each column and then
                # sorting using the previously computed row index list
                cols = D.argmin(axis=1)[rows]

                # in order to determine if we need to update, register,
                # or deregister an object we need to keep track of which
                # of the rows and column indexes we have already examined
                usedRows = set()
                usedCols = set()

                # loop over the combination of the (row, column) index
                # tuples
                for (row, col) in zip(rows, cols):
                    # if we have already examined either the row or
                    # column value before, ignore it
                    # val
                    if row in usedRows or col in usedCols:
                        continue

                    # otherwise, grab the object for the current row,
                    # set its new centroid, and reset the disappeared
                    # counter
                    # objectID = objectIDs[row]
                    # self.objects[objectID] = inputCentroids[col]
                    # self.disappeared[objectID] = 0
                    try:
                        objects[row].appear(rects[col])

                        # indicate that we have examined each of the row and
                        # column indexes, respectively
                        usedRows.add(row)
                        usedCols.add(col)

                    except KeyError as ke:
                        logging.error(ke)
        except KeyError as ke:
            logging.error(ke)

        for tracked in self.objects.difference(self.seen):
            tracked.disappear()

        # return the set of trackable objects
        return self.objects
