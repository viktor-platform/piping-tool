# pylint: disable=W1401
import copy
from typing import Optional

from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import Point

from viktor.geometry import Point as ViktorPoint
from viktor.geometry import Polyline as ViktorPolyline


def _get_first_point_from_intersection_of_lines(line1, line2) -> Point:
    """
    Function to get only the first point from the intersection of 2 lines.
    - line1 : LineString
    - line2 : LineString

    Returns first point intersection : Point
    """

    intersection = line1.intersection(line2)
    if intersection.type == "Point":
        return intersection
    elif intersection.type == "MultiPoint":
        return list(intersection)[0]
    else:
        raise DitchIntersectionLines("Intersection type not recognized")


class Ditch:
    def __init__(
        self,
        left_point_top: dict,
        left_point_bottom: dict,
        right_point_bottom: dict,
        right_point_top: dict,
        is_wet: bool,
        depth: Optional[float] = None,  # water depth or maintenance depth
        talu_slope: Optional[float] = None,  # slope of the ditch
    ):
        """
        Base class that defines ditch properties.

                  __________
                /           \
              /              \
            /                 \____ 1     B     4 _____
                                    \          /
                                    2\______ /3
                                          b

        - left_point_top:     Point 1 in drawing
        - left_point_bottom:  Point 2 in drawing
        - right_point_bottom: Point 3 in drawing
        - right_point_top:    Point 4 in drawing
        - is_wet: Set to True if there is water in the ditch
        """

        self.left_point_top = Point(left_point_top["x"], left_point_top["z"])
        self.left_point_bottom = Point(left_point_bottom["x"], left_point_bottom["z"])
        self.right_point_bottom = Point(right_point_bottom["x"], right_point_bottom["z"])
        self.right_point_top = Point(right_point_top["x"], right_point_top["z"])
        self.is_wet = is_wet
        self.case = None
        self.depth = depth
        self.talu_slope = talu_slope

    @classmethod
    def from_intersection(
        cls, left_edge: Point, right_edge: Point, ditch_dict: dict, origin_point: Point, polderpeil: float
    ):
        """
        create a ditch from the intersection of a cross section and the ditch polygon,
        depth can be either water depth or maintenance level, depending on need
        - left edge: coordinates in RD
        - right edge:  coordinates in RD
        - ditch_dict: ditch dict from segment params
        - origin_point: origin (in RD) of the cross section: point where x == 0
        """
        if right_edge.distance(origin_point) < left_edge.distance(origin_point):
            temp = copy.copy(right_edge)  # switch if needed
            right_edge = left_edge
            left_edge = temp

        depth = ditch_dict["water_depth"]
        slope = ditch_dict["talu_slope"]

        left_top = {"x": left_edge.distance(origin_point), "z": polderpeil}
        left_bot = {"x": left_top["x"] + depth / slope, "z": polderpeil - depth}

        right_top = {"x": right_edge.distance(origin_point), "z": polderpeil}
        right_bot = {"x": right_top["x"] - depth / slope, "z": polderpeil - depth}

        return cls(left_top, left_bot, right_bot, right_top, is_wet=ditch_dict["is_wet"], depth=depth, talu_slope=slope)

    def surface_line(self, extend=20) -> LineString:
        """
        Surface line obtained with ditch points.
        - extend: extend surface line to the left and right of the ditch, needed for H3. [m]
        - returns: Linestring as follows    _____     _____
                                                 \___/
        """
        return LineString(
            [
                Point(self.left_point_top.x - extend, self.left_point_top.y),
                self.left_point_top,
                self.left_point_bottom,
                self.right_point_bottom,
                self.right_point_top,
                Point(self.right_point_top.x + extend, self.right_point_top.y),
            ]
        )

    @property
    def cross_section(self) -> ViktorPolyline:
        """viktor polyline to describe the cross section of the ditch, no extension to the sides
        \       /
         \____/
        """
        return ViktorPolyline(
            [
                ViktorPoint(self.left_point_top.x, self.left_point_top.y),
                ViktorPoint(self.left_point_bottom.x, self.left_point_bottom.y),
                ViktorPoint(self.right_point_bottom.x, self.right_point_bottom.y),
                ViktorPoint(self.right_point_top.x, self.right_point_top.y),
            ]
        )

    @property
    def large_b(self) -> float:
        # TODO: explain?
        if self.left_point_top.y >= self.right_point_top.y:  # pylint: disable=no-else-raise
            line_ditch = LineString(
                [
                    (self.left_point_top.x, self.right_point_top.y),
                    self.right_point_top,
                ]
            )
            if isinstance(self.surface_line().intersection(line_ditch), MultiPoint):
                point_left_ditch = self.surface_line().intersection(line_ditch).geoms[0]
                return self.right_point_top.x - point_left_ditch.x
            # sometimes, self.surface_line().intersection(line_ditch) returns a single Point, what does it mean from
            # a physical point of view? For now this case is simply considered as invalid and no unity check is returned
            raise DitchLargeBError
        else:
            line_ditch = LineString(
                [
                    self.left_point_top,
                    (self.right_point_top.x, self.left_point_top.y),
                ]
            )
            if isinstance(self.surface_line().intersection(line_ditch), MultiPoint):
                point_right_ditch = self.surface_line().intersection(line_ditch).geoms[1]
                return point_right_ditch.x - self.left_point_top.x
            # sometimes, self.surface_line().intersection(line_ditch) returns a single Point, what does it mean from
            # a physical point of view? For now this case is simply considered as invalid and no unity check is returned
            raise DitchLargeBError

    @property
    def small_b(self) -> float:
        # TODO: explain?
        return self.right_point_bottom.x - self.left_point_bottom.x

    def h1(self, z_aquifer: float) -> float:

        return self.right_point_top.y - z_aquifer

    def h2(self, z_aquifer: float) -> float:
        return self.right_point_bottom.y - z_aquifer

    def h3(self, z_aquifer: float, dist=20) -> float:
        """If the slope of the talu is less than 2:1, then there is a trigonometric literal expression of h3.
        If the slope of the talu is more than 2:1, h4 is determined from line intersections."""
        if self.talu_slope < 2:
            h2 = self.h2(z_aquifer)
            b = self.small_b
            return 2 * (h2 - b / (2 * self.talu_slope)) / (2 - 1 / self.talu_slope)
        else:
            mid_point = Point(
                (self.right_point_bottom.x + self.left_point_bottom.x) / 2,
                min(self.right_point_bottom.y, self.left_point_bottom.y),
            )
            right_line = LineString(
                [
                    Point(mid_point.x, z_aquifer),
                    Point(mid_point.x + dist, z_aquifer + dist * 2),  # inclination 1: 2
                ]
            )
            right_point = _get_first_point_from_intersection_of_lines(self.surface_line(), right_line)

            left_line = LineString(
                [
                    Point(mid_point.x, z_aquifer),
                    Point(mid_point.x - dist, z_aquifer + dist * 2),
                ]
            )
            left_point = _get_first_point_from_intersection_of_lines(self.surface_line(), left_line)
            if left_point.y < right_point.y:
                point = left_point
            else:
                point = right_point
            return point.y - z_aquifer

    def h_eff(self, z_aquifer: float) -> float:
        """
        Height that should be used in the calculation of uplift.
        Returns
        -------

        """
        if self.h1(z_aquifer) >= self.large_b:
            self.case = "h1"
            return self.h1(z_aquifer)
        elif self.h2(z_aquifer) <= self.small_b:
            self.case = "h2"
            return self.h2(z_aquifer)
        elif self.small_b < self.h2(z_aquifer) <= self.large_b:
            self.case = "h3"
            return self.h3(z_aquifer)
        else:
            raise DitchHeffError(
                f"H1={self.h1}, H2={self.h2}, H3={self.h2}, B={self.large_b}, b={self.small_b} "
                f"met deze waarden kan er geen TRWD worden uitgevoerd"
            )


class DitchHeffError(Exception):
    """Custom error for the case where h_eff cannot be calculated with the provided ditch input."""


class DitchLargeBError(Exception):
    """Custom error for the case where large_b cannot be calculated"""


class DitchIntersectionLines(ValueError):
    """Custom error for the function _get_first_point_from_intersection_of_lines"""
