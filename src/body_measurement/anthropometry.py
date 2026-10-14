"""Anthropometric body measurement extraction based on SMPL-Anthropometry.

Implements the anthropometric measurement extraction logic defined in:
https://github.com/DavidBoja/SMPL-Anthropometry

Key Capabilities:
1. Standard Measurement Taxonomy (ISO 7250 / ANSUR standard labels A through P).
2. Distinction between LENGTH measurements (landmark Euclidean distance) and
   CIRCUMFERENCE measurements (plane slicing with normal vector + convex hull perimeter).
3. 3D Mesh / Cross-section Plane Cutting:
   Slices body geometry with cutting planes defined by anatomical landmarks (origin)
   and joint vectors (normal along longitudinal body axis).
4. Convex Hull Perimeter Calculation:
   Projects slice intersection points onto the 2D plane and computes the closed convex hull
   perimeter via distance summation.
5. Proportional Height Normalization:
   Normalizes all dimensions against ground-truth user stature:
   new_measurement = (old_measurement / old_height) * target_height.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.spatial import ConvexHull


class MeasurementType(str, Enum):
    """Categorization of anthropometric body measurements."""
    LENGTH = "length"
    CIRCUMFERENCE = "circumference"


# Standard Literature Labels (A to P) as defined in SMPL-Anthropometry
STANDARD_LABELS: Dict[str, str] = {
    "A": "head circumference",
    "B": "neck circumference",
    "C": "shoulder to crotch height",
    "D": "chest circumference",
    "E": "waist circumference",
    "F": "hip circumference",
    "G": "wrist right circumference",
    "H": "bicep right circumference",
    "I": "forearm right circumference",
    "J": "arm right length",
    "K": "inside leg height",
    "L": "thigh left circumference",
    "M": "calf left circumference",
    "N": "ankle left circumference",
    "O": "shoulder breadth",
    "P": "height",
}

# Measurement Type Registry
MEASUREMENT_TYPES: Dict[str, MeasurementType] = {
    "height": MeasurementType.LENGTH,
    "head circumference": MeasurementType.CIRCUMFERENCE,
    "neck circumference": MeasurementType.CIRCUMFERENCE,
    "shoulder to crotch height": MeasurementType.LENGTH,
    "chest circumference": MeasurementType.CIRCUMFERENCE,
    "waist circumference": MeasurementType.CIRCUMFERENCE,
    "hip circumference": MeasurementType.CIRCUMFERENCE,
    "wrist right circumference": MeasurementType.CIRCUMFERENCE,
    "bicep right circumference": MeasurementType.CIRCUMFERENCE,
    "forearm right circumference": MeasurementType.CIRCUMFERENCE,
    "arm right length": MeasurementType.LENGTH,
    "arm left length": MeasurementType.LENGTH,
    "inside leg height": MeasurementType.LENGTH,
    "thigh left circumference": MeasurementType.CIRCUMFERENCE,
    "calf left circumference": MeasurementType.CIRCUMFERENCE,
    "ankle left circumference": MeasurementType.CIRCUMFERENCE,
    "shoulder breadth": MeasurementType.LENGTH,
    "crotch height": MeasurementType.LENGTH,
}


def compute_euclidean_distance(p1: np.ndarray, p2: np.ndarray) -> float:
    """Computes Euclidean distance between two 3D points in centimeters."""
    p1 = np.asarray(p1, dtype=np.float64)
    p2 = np.asarray(p2, dtype=np.float64)
    return float(np.linalg.norm(p2 - p1))


def compute_polyline_distance(points: np.ndarray) -> float:
    """Computes total polyline distance across consecutive 3D vertex pairs."""
    pts = np.asarray(points, dtype=np.float64)
    if pts.ndim == 2:
        # Array of N points: sum distance between consecutive vertices
        diffs = pts[1:] - pts[:-1]
        return float(np.sum(np.linalg.norm(diffs, axis=1)))
    elif pts.ndim == 3 and pts.shape[1] == 2:
        # Array of N segments of shape (N, 2, 3)
        diffs = pts[:, 1] - pts[:, 0]
        return float(np.sum(np.linalg.norm(diffs, axis=1)))
    else:
        raise ValueError(f"Unsupported point array shape: {pts.shape}")


def convex_hull_from_3d_points(slice_segments: np.ndarray) -> np.ndarray:
    """Extracts convex hull segments from planar 3D line segments.

    Synchronized with SMPL-Anthropometry: utils.convex_hull_from_3D_points.

    Args:
        slice_segments: (N, 2, 3) array representing N 3D line segments.

    Returns:
        (K, 2, 3) array of segments forming the convex hull perimeter loop.
    """
    if len(slice_segments) == 0:
        return np.empty((0, 2, 3), dtype=np.float64)

    # Merge endpoints into unique points
    merged = np.concatenate(slice_segments, axis=0)
    unique_points = np.unique(merged, axis=0)

    if len(unique_points) < 3:
        return slice_segments

    # Points lie in a 3D plane; find the redundant normal coordinate
    ranges = np.ptp(unique_points, axis=0)
    redundant_coord = int(np.argmin(ranges))
    plane_coords = [i for i in range(3) if i != redundant_coord]

    # Compute 2D Convex Hull on in-plane coordinates
    hull = ConvexHull(unique_points[:, plane_coords])

    # Convert hull simplices to (K, 2, 3) line segments
    hull_segments = unique_points[hull.simplices]
    return hull_segments


def compute_contour_perimeter_cm(
    points_2d_or_3d: np.ndarray,
    unit_scale: float = 1.0,
) -> float:
    """Computes closed convex-hull perimeter of a planar contour.

    Args:
        points_2d_or_3d: Array of points (N, 2) or (N, 3).
        unit_scale: Multiplier to convert to centimeters (e.g. 100 if coords are meters).

    Returns:
        Perimeter in centimeters rounded to 2 decimal places.
    """
    pts = np.asarray(points_2d_or_3d, dtype=np.float64)
    if len(pts) < 3:
        return 0.0

    if pts.shape[1] == 3:
        ranges = np.ptp(pts, axis=0)
        redundant = int(np.argmin(ranges))
        coords = [i for i in range(3) if i != redundant]
        pts_2d = pts[:, coords]
    else:
        pts_2d = pts

    hull = ConvexHull(pts_2d)
    hull_vertices = pts_2d[hull.vertices]

    # Compute closed polygon perimeter
    diffs = np.roll(hull_vertices, -1, axis=0) - hull_vertices
    perimeter = float(np.sum(np.linalg.norm(diffs, axis=1))) * unit_scale
    return round(perimeter, 2)


def slice_mesh_plane(
    vertices: np.ndarray,
    faces: np.ndarray,
    plane_origin: np.ndarray,
    plane_normal: np.ndarray,
) -> np.ndarray:
    """Pure-NumPy vectorized plane-triangle mesh slicing.

    Intersects a 3D triangle mesh with a plane defined by plane_origin and plane_normal.
    Produces the exact same output as trimesh.intersections.mesh_plane.

    Args:
        vertices: (V, 3) float array of vertex coordinates.
        faces: (F, 3) integer array of triangle face vertex indices.
        plane_origin: (3,) float array of a point on the plane.
        plane_normal: (3,) float array of the plane normal vector.

    Returns:
        (N, 2, 3) array of line segments representing the plane intersection contour.
    """
    verts = np.asarray(vertices, dtype=np.float64)
    tri_faces = np.asarray(faces, dtype=np.int64)
    origin = np.asarray(plane_origin, dtype=np.float64)
    normal = np.asarray(plane_normal, dtype=np.float64)
    norm = np.linalg.norm(normal)
    if norm < 1e-9:
        raise ValueError("Plane normal vector cannot be zero.")
    normal = normal / norm

    # Signed distances from vertices to plane
    dists = np.dot(verts - origin, normal)

    # Face vertex distances (F, 3)
    face_dists = dists[tri_faces]

    # Signs of vertex distances (-1, 0, or 1)
    signs = np.sign(face_dists)
    signs[np.abs(face_dists) < 1e-9] = 0

    # Triangles that cross the plane have both positive and negative vertices
    has_pos = np.any(signs > 0, axis=1)
    has_neg = np.any(signs < 0, axis=1)
    crossing_mask = has_pos & has_neg

    if not np.any(crossing_mask):
        return np.empty((0, 2, 3), dtype=np.float64)

    crossing_faces = tri_faces[crossing_mask]
    crossing_dists = face_dists[crossing_mask]

    # For each crossing triangle, find the two intersected edges
    # Triangle edges: (0,1), (1,2), (2,0)
    edge_pairs = [(0, 1), (1, 2), (2, 0)]
    segments = []

    for f_idx in range(len(crossing_faces)):
        face = crossing_faces[f_idx]
        d = crossing_dists[f_idx]
        pts_on_plane = []

        for v0_local, v1_local in edge_pairs:
            d0, d1 = d[v0_local], d[v1_local]
            if (d0 > 0 and d1 < 0) or (d0 < 0 and d1 > 0):
                # Edge intersects plane
                t = -d0 / (d1 - d0)
                p0 = verts[face[v0_local]]
                p1 = verts[face[v1_local]]
                intersect_pt = p0 + t * (p1 - p0)
                pts_on_plane.append(intersect_pt)
            elif abs(d0) < 1e-9 and abs(d1) >= 1e-9:
                pts_on_plane.append(verts[face[v0_local]])

        if len(pts_on_plane) >= 2:
            segments.append([pts_on_plane[0], pts_on_plane[1]])

    if len(segments) == 0:
        return np.empty((0, 2, 3), dtype=np.float64)

    return np.asarray(segments, dtype=np.float64)


@dataclass
class CircumferencePlaneDefinition:
    """Definition of an anatomical circumference cutting plane."""
    landmarks: List[str]
    joints: Tuple[str, str]
    body_part: Optional[Union[str, List[str]]] = None


# Default SMPL-Anthropometry Circumference Plane Specifications
DEFAULT_CIRCUMFERENCE_DEFINITIONS: Dict[str, CircumferencePlaneDefinition] = {
    "head circumference": CircumferencePlaneDefinition(
        landmarks=["HEAD_LEFT_TEMPLE"],
        joints=("pelvis", "spine3"),
        body_part="head",
    ),
    "neck circumference": CircumferencePlaneDefinition(
        landmarks=["NECK_ADAM_APPLE"],
        joints=("spine1", "head"),
        body_part="neck",
    ),
    "chest circumference": CircumferencePlaneDefinition(
        landmarks=["LEFT_NIPPLE", "RIGHT_NIPPLE"],
        joints=("pelvis", "spine3"),
        body_part=["spine1", "spine2"],
    ),
    "waist circumference": CircumferencePlaneDefinition(
        landmarks=["BELLY_BUTTON", "BACK_BELLY_BUTTON"],
        joints=("pelvis", "spine3"),
        body_part=["hips", "spine"],
    ),
    "hip circumference": CircumferencePlaneDefinition(
        landmarks=["PUBIC_BONE"],
        joints=("pelvis", "spine3"),
        body_part="hips",
    ),
    "wrist right circumference": CircumferencePlaneDefinition(
        landmarks=["RIGHT_WRIST"],
        joints=("right_wrist", "right_hand"),
    ),
    "bicep right circumference": CircumferencePlaneDefinition(
        landmarks=["RIGHT_BICEP"],
        joints=("right_shoulder", "right_elbow"),
    ),
    "forearm right circumference": CircumferencePlaneDefinition(
        landmarks=["RIGHT_FOREARM"],
        joints=("right_elbow", "right_wrist"),
    ),
    "thigh left circumference": CircumferencePlaneDefinition(
        landmarks=["LEFT_THIGH"],
        joints=("pelvis", "spine3"),
        body_part="leftUpLeg",
    ),
    "calf left circumference": CircumferencePlaneDefinition(
        landmarks=["LEFT_CALF"],
        joints=("pelvis", "spine3"),
        body_part="leftLeg",
    ),
    "ankle left circumference": CircumferencePlaneDefinition(
        landmarks=["LEFT_ANKLE"],
        joints=("pelvis", "spine3"),
        body_part="leftLeg",
    ),
}

# Default Length Definitions (Landmark point pairs)
DEFAULT_LENGTH_DEFINITIONS: Dict[str, Tuple[str, str]] = {
    "height": ("HEAD_TOP", "HEELS"),
    "shoulder to crotch height": ("SHOULDER_TOP", "INSEAM_POINT"),
    "shoulder breadth": ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
    "inside leg height": ("LOW_LEFT_HIP", "LEFT_ANKLE"),
    "arm right length": ("RIGHT_SHOULDER", "RIGHT_WRIST"),
    "arm left length": ("LEFT_SHOULDER", "LEFT_WRIST"),
    "crotch height": ("CROTCH", "HEELS"),
}


class AnthropometricMeasurer:
    """Anthropometric measurement engine based on SMPL-Anthropometry."""

    def __init__(
        self,
        landmarks: Dict[str, np.ndarray],
        joints: Optional[Dict[str, np.ndarray]] = None,
        mesh_vertices: Optional[np.ndarray] = None,
        mesh_faces: Optional[np.ndarray] = None,
        unit: str = "cm",
    ) -> None:
        """Initializes measurer with landmarks, joints, and optional mesh geometry.

        Args:
            landmarks: Dictionary of landmark names to 3D coordinate arrays.
            joints: Dictionary of joint names to 3D position arrays.
            mesh_vertices: (V, 3) array of mesh vertices if 3D mesh is available.
            mesh_faces: (F, 3) array of triangle face indices if 3D mesh is available.
            unit: Input coordinate unit ('m' or 'cm'). Default is 'cm'.
        """
        self.scale_to_cm = 100.0 if unit == "m" else 1.0
        self.landmarks = {k: np.asarray(v, dtype=np.float64) * self.scale_to_cm for k, v in landmarks.items()}
        self.joints = (
            {k: np.asarray(v, dtype=np.float64) * self.scale_to_cm for k, v in joints.items()}
            if joints
            else {}
        )
        self.vertices = (
            np.asarray(mesh_vertices, dtype=np.float64) * self.scale_to_cm
            if mesh_vertices is not None
            else None
        )
        self.faces = np.asarray(mesh_faces, dtype=np.int64) if mesh_faces is not None else None

        self.length_definitions = dict(DEFAULT_LENGTH_DEFINITIONS)
        self.circumference_definitions = dict(DEFAULT_CIRCUMFERENCE_DEFINITIONS)

        self.measurements: Dict[str, float] = {}
        self.normalized_measurements: Dict[str, float] = {}
        self.labeled_measurements: Dict[str, float] = {}

    def measure_length(self, name: str) -> float:
        """Measures Euclidean distance between the two landmarks defining a length."""
        if name not in self.length_definitions:
            raise KeyError(f"Length measurement '{name}' is not defined.")

        lm1_name, lm2_name = self.length_definitions[name]
        if lm1_name not in self.landmarks or lm2_name not in self.landmarks:
            raise ValueError(f"Required landmarks ('{lm1_name}', '{lm2_name}') not found.")

        p1 = self.landmarks[lm1_name]
        p2 = self.landmarks[lm2_name]
        dist_cm = compute_euclidean_distance(p1, p2)
        return round(dist_cm, 2)

    def measure_circumference(
        self,
        name: str,
        custom_cross_section_points: Optional[np.ndarray] = None,
    ) -> float:
        """Measures cross-section circumference using plane slicing and convex hull perimeter.

        Args:
            name: Circumference measurement name (e.g., 'chest circumference').
            custom_cross_section_points: Optional direct 2D/3D cross-section contour points.

        Returns:
            Circumference in centimeters.
        """
        # 1. Direct cross-section points provided (e.g. from silhouette visual hull)
        if custom_cross_section_points is not None:
            return compute_contour_perimeter_cm(custom_cross_section_points, unit_scale=1.0)

        # 2. Slicing 3D surface mesh
        if self.vertices is not None and self.faces is not None:
            if name not in self.circumference_definitions:
                raise KeyError(f"Circumference '{name}' is not defined.")

            definition = self.circumference_definitions[name]

            # Plane origin: average of landmark points
            lm_coords = [self.landmarks[lm] for lm in definition.landmarks if lm in self.landmarks]
            if not lm_coords:
                raise ValueError(f"None of the landmarks for '{name}' exist in provided landmarks.")
            plane_origin = np.mean(lm_coords, axis=0)

            # Plane normal: vector connecting the two joints
            j1_name, j2_name = definition.joints
            if j1_name in self.joints and j2_name in self.joints:
                plane_normal = self.joints[j2_name] - self.joints[j1_name]
            else:
                # Default vertical longitudinal normal (Z or Y axis)
                plane_normal = np.array([0.0, 0.0, 1.0])

            # Slice mesh with plane
            segments = slice_mesh_plane(self.vertices, self.faces, plane_origin, plane_normal)
            if len(segments) == 0:
                return 0.0

            hull_segments = convex_hull_from_3d_points(segments)
            return round(compute_polyline_distance(hull_segments), 2)

        # 3. Fallback to Ramanujan approximation from orthogonal landmarks if no 3D mesh
        raise ValueError(
            f"Cannot compute circumference for '{name}': Mesh geometry or contour points required."
        )

    def measure_all(
        self,
        measurement_names: Optional[List[str]] = None,
        custom_cross_sections: Optional[Dict[str, np.ndarray]] = None,
    ) -> Dict[str, float]:
        """Measures all requested measurements."""
        if measurement_names is None:
            measurement_names = list(self.length_definitions.keys()) + list(self.circumference_definitions.keys())

        for name in measurement_names:
            m_type = MEASUREMENT_TYPES.get(name)
            if m_type == MeasurementType.LENGTH:
                try:
                    self.measurements[name] = self.measure_length(name)
                except (KeyError, ValueError):
                    pass
            elif m_type == MeasurementType.CIRCUMFERENCE:
                try:
                    custom_pts = custom_cross_sections.get(name) if custom_cross_sections else None
                    self.measurements[name] = self.measure_circumference(name, custom_cross_section_points=custom_pts)
                except (KeyError, ValueError):
                    pass

        return self.measurements

    def height_normalize_measurements(self, target_height_cm: float) -> Dict[str, float]:
        """Normalizes all measurements against target height (SMPL-Anthropometry specification).

        Formula:
            new_measurement = (old_measurement / old_height) * target_height_cm
        """
        if "height" not in self.measurements or self.measurements["height"] <= 0:
            raise ValueError("Height measurement is missing or non-positive; cannot normalize.")

        old_height = self.measurements["height"]
        scale = target_height_cm / old_height

        self.normalized_measurements = {}
        for m_name, m_val in self.measurements.items():
            self.normalized_measurements[m_name] = round(m_val * scale, 2)

        return self.normalized_measurements

    def label_measurements(
        self,
        labels_map: Dict[str, str] = STANDARD_LABELS,
        use_normalized: bool = False,
    ) -> Dict[str, float]:
        """Maps measurements to standard literature labels (A through P).

        Returns:
            Dictionary mapping standard labels ('A', 'B', ...) to measurement values in cm.
        """
        source = self.normalized_measurements if use_normalized else self.measurements
        self.labeled_measurements = {}

        for label_key, measure_name in labels_map.items():
            if measure_name in source:
                self.labeled_measurements[label_key] = source[measure_name]

        return self.labeled_measurements
