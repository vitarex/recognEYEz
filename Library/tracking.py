# import the necessary packages
from scipy.spatial import distance as dist
from scipy.optimize import linear_sum_assignment
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

def normalize(a):
    """Normalize numpy array

    Arguments:
        a -- Numpy array to normalize
    """
    norm = np.linalg.norm(a, ord=1)
    if norm == 0:
        norm = np.max(a)
    if norm == 0:
        return a
    return a/norm

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
        """Increment the tracked object's disappearance counter, and if it becomes larger than the
        limit, remove it from tracking
        """
        self.disappearCount += 1
        if self.disappearCount > self.maxDisappeared:
            self.tracker.deregister(self)

    def appear(self, rect, cent=None):
        """Record a new position of appearance for a tracked object

        Arguments:
            rect {Tuple} -- The bounding box of the face

        Keyword Arguments:
            cent {Tuple} -- The centroid point, if it has already been calculated (default: {None})
        """
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

        # there is a decision here whether to clear the current object registry
        # if we clear it, previous tracked people who are on the disappeared list are erased,
        # even though they could appear again before the next run
        # if we don't clear it, the previous tracking objects might interfere with the new ones
        # by "stealing" their place when they overlap
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

    def update(self, rects: List[Tuple[int]]) -> Set[TrackedPerson]:
        """Attempt to pair the face bounding boxes from the current frame with the centroids in the registry
        and update the registry accordingly. People that disappear for too many frames are removed from the registry.

        Arguments:
            rects -- Face bounding rectangles in (top, right, bottom, left) order

        Returns:
            List -- List of tuples of face bounding boxes and their respective person
        """
        # clear the objects seen on the previous frame
        self.seen.clear()

        # create a list from our objects to define an order on them
        objects = list(self.objects)
        objects: List[TrackedPerson]

        # check to see if the list of input bounding box rectangles
        # is empty
        if len(rects) == 0:
            # loop over any existing tracked objects and mark them
            # as disappeared
            # and don't loop over the set itself, since the collection is
            # modified ;)
            for tracked in objects:
                tracked.disappear()

            # return early as there are no centroids or tracking info
            # to update
            return self.objects

        # initialize an array of input centroids for the current frame
        inputCentroids = np.zeros((len(rects), 2), dtype="int")

        # use the bounding box coordinates to derive the centroids
        inputCentroids = [centroid(rect) for rect in rects]

        objectCentroids = list()
        objectRects = list()
        objectAges = list()

        # create lists of their attributes with the same order
        for tracked in self.objects:
            objectCentroids.append(tracked.centroid)
            objectRects.append(tracked.rect)
            objectAges.append(tracked.disappearCount)

        try:
            if len(self.objects) == 0:
                return self.objects

            # otherwise, we are currently tracking objects so we need to
            # try to match the input centroids to existing object
            # centroids
            else:
                # compute a distance value between each pair of tracked object and new objects,
                # respectively -- our goal will be to match an input centroid to an existing
                # object centroid

                # the second and third components are important two counteract the "stealing" phenomenon
                # when a disappeared face incorrectly replaces a correctly tracked one because the correctly tracked face
                # moves to close to the old one
                # another effective way against this would be to detect exchanges like this explicitly by looking at the
                # position of the disappearing and reappearing faces
                # if there is a frame where a face disappears and an old one reappears very close by, it might be
                # an erroneous replacement of this kind

                # the first distance component is the euclidean distance in the 2D space
                # this component is normalized, since it is dependent on the camera resolution
                D1 = normalize(dist.cdist(np.array(objectCentroids), inputCentroids))

                # the second component is the size difference of the bounding boxes
                # the same face is likely to be similar in size across subsequent frames
                # this component is normalized, since it is dependent on the camera resolution (by the second order)
                # take the bounding boxes as a row vector
                orects = np.array(objectRects)
                # first we calculate the areas of the boxes by calculating  the sides and multiplying them
                oareas = (np.array((orects[..., 2] - orects[..., 0], orects[..., 1] - orects[..., 3])).T).prod(axis=-1)
                # do this for the new faces as well
                nrects = np.array(rects)
                nareas = (np.array((nrects[..., 2] - nrects[..., 0], nrects[..., 1] - nrects[..., 3])).T).prod(axis=-1)
                # finally, the distance matrix is calculated and normalized
                # the distance matrix expects a 2d array, so we create column vectors from the row vectors
                D2 = normalize(dist.cdist(oareas[np.newaxis].T, nareas[np.newaxis].T))

                # the third component is the age of the tracked object mapped to [0.5, 1]
                D3 = (np.array(objectAges) + self.maxDisappeared) / (self.maxDisappeared * 2)

                # the first two components are multiplied elementwise, while the third
                # is applied as a vector across the rows of the matrix
                D = (np.multiply(D1, D2)) * D3[:, np.newaxis]

                # the maximum number of pairs is given by min(len(objectCentroids), len(inputCentroids))
                # we minimize the distance cost for this number of pairs using the hungarian algorithm
                min_indexes = linear_sum_assignment(D)

                # let's take the pairs with the minimum distance cost
                # and update the corresponding tracked objects
                for i in range(min(len(objectCentroids), len(inputCentroids))):
                    objects[min_indexes[0][i]].appear(rects[min_indexes[1][i]])

                # if there are more new faces than old faces, we don't do anything else
                # this can occur when force_dnn_on_new is turned off and a new face appears
                # since we don't know yet who this face belongs to, we don't start tracking it

                # however, if there are more old faces than new, we must mark the ones
                # not paired with a new face as having disappeared
                for i in [x for x in range(len(objectCentroids)) if x not in min_indexes[0]]:
                    objects[i].disappear()

        except KeyError as ke:
            logging.error(ke)

        # return the set of trackable objects
        return self.objects
