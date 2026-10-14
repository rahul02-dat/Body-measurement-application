"""Unit tests for SMPL-Anthropometry measurement extraction logic."""

import math
import numpy as np
import pytest

from body_measurement.anthropometry import (
    AnthropometricMeasurer,
    compute_contour_perimeter_cm,
    compute_euclidean_distance,
    compute_polyline_distance,
    slice_mesh_plane,
    STANDARD_LABELS,
)


def test_euclidean_and_polyline_distance():
    """Verify basic metric distance calculations."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([3.0, 4.0, 0.0])
    dist = compute_euclidean_distance(p1, p2)
    assert pytest.approx(dist, rel=1e-5) == 5.0

    # Polyline: (0,0) -> (3,4) -> (3,8) = 5 + 4 = 9
    pts = np.array([[0.0, 0.0, 0.0], [3.0, 4.0, 0.0], [3.0, 8.0, 0.0]])
    poly_dist = compute_polyline_distance(pts)
    assert pytest.approx(poly_dist, rel=1e-5) == 9.0


def test_convex_hull_perimeter_known_circle():
    """Verify convex hull perimeter of points sampled along a circle with radius R."""
    radius = 10.0  # cm
    expected_circumference = 2.0 * math.pi * radius  # ~62.83 cm

    # Sample 72 points along circle perimeter
    angles = np.linspace(0, 2 * math.pi, 72, endpoint=False)
    circle_pts = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])

    perimeter = compute_contour_perimeter_cm(circle_pts)
    # 72-gon is slightly less than circle: ~62.79 cm vs 62.83 cm
    assert pytest.approx(perimeter, abs=0.2) == expected_circumference


def test_slice_mesh_plane_cylinder():
    """Verify plane slicing through a vertical triangular prism mesh."""
    # Create a 4-sided vertical prism (extruded box)
    vertices = np.array([
        # Bottom square at z = 0
        [-10.0, -10.0, 0.0],
        [10.0, -10.0, 0.0],
        [10.0, 10.0, 0.0],
        [-10.0, 10.0, 0.0],
        # Top square at z = 100
        [-10.0, -10.0, 100.0],
        [10.0, -10.0, 100.0],
        [10.0, 10.0, 100.0],
        [-10.0, 10.0, 100.0],
    ])

    # Side wall triangles
    faces = np.array([
        [0, 1, 5], [0, 5, 4],  # front wall
        [1, 2, 6], [1, 6, 5],  # right wall
        [2, 3, 7], [2, 7, 6],  # back wall
        [3, 0, 4], [3, 4, 7],  # left wall
    ])

    plane_origin = np.array([0.0, 0.0, 50.0])
    plane_normal = np.array([0.0, 0.0, 1.0])

    segments = slice_mesh_plane(vertices, faces, plane_origin, plane_normal)
    assert len(segments) == 8  # 2 triangles per wall * 4 walls = 8 segments

    # Perimeter of 20x20 square is 80 cm
    pts = np.concatenate(segments, axis=0)
    perimeter = compute_contour_perimeter_cm(pts)
    assert pytest.approx(perimeter, abs=0.1) == 80.0


def test_anthropometric_measurer_lengths_and_normalization():
    """Verify AnthropometricMeasurer lengths, height normalization, and standard labels."""
    landmarks = {
        "HEAD_TOP": np.array([0.0, 0.0, 180.0]),
        "HEELS": np.array([0.0, 0.0, 0.0]),
        "SHOULDER_TOP": np.array([0.0, 0.0, 150.0]),
        "INSEAM_POINT": np.array([0.0, 0.0, 80.0]),
        "LEFT_SHOULDER": np.array([-22.0, 0.0, 145.0]),
        "RIGHT_SHOULDER": np.array([22.0, 0.0, 145.0]),
        "LOW_LEFT_HIP": np.array([-10.0, 0.0, 85.0]),
        "LEFT_ANKLE": np.array([-10.0, 0.0, 8.0]),
    }

    joints = {
        "pelvis": np.array([0.0, 0.0, 90.0]),
        "spine3": np.array([0.0, 0.0, 140.0]),
    }

    measurer = AnthropometricMeasurer(landmarks=landmarks, joints=joints, unit="cm")

    # Height: 180 - 0 = 180.0 cm
    height = measurer.measure_length("height")
    assert pytest.approx(height, rel=1e-5) == 180.0

    # Shoulder breadth: 22 - (-22) = 44.0 cm
    shoulder_breadth = measurer.measure_length("shoulder breadth")
    assert pytest.approx(shoulder_breadth, rel=1e-5) == 44.0

    # Inside leg height: 85 - 8 = 77.0 cm
    inseam = measurer.measure_length("inside leg height")
    assert pytest.approx(inseam, rel=1e-5) == 77.0

    # Shoulder to crotch height: 150 - 80 = 70.0 cm
    trunk_ht = measurer.measure_length("shoulder to crotch height")
    assert pytest.approx(trunk_ht, rel=1e-5) == 70.0

    # Add custom cross-section for chest (ellipse with a=16, b=12 -> ~88.4 cm)
    angles = np.linspace(0, 2 * math.pi, 60, endpoint=False)
    chest_pts = np.column_stack([16.0 * np.cos(angles), 12.0 * np.sin(angles)])
    custom_slices = {"chest circumference": chest_pts}

    measurer.measure_all(custom_cross_sections=custom_slices)
    assert "chest circumference" in measurer.measurements
    assert measurer.measurements["chest circumference"] > 80.0

    # Height normalization: target 175 cm (scale = 175 / 180 = ~0.9722)
    norm = measurer.height_normalize_measurements(target_height_cm=175.0)
    assert pytest.approx(norm["height"], abs=0.01) == 175.0
    assert pytest.approx(norm["shoulder breadth"], abs=0.1) == 44.0 * (175.0 / 180.0)

    # Label measurements using standard literature mapping
    labeled = measurer.label_measurements(labels_map=STANDARD_LABELS, use_normalized=True)
    assert "P" in labeled  # 'P' is height
    assert pytest.approx(labeled["P"], abs=0.01) == 175.0
    assert "O" in labeled  # 'O' is shoulder breadth
    assert "D" in labeled  # 'D' is chest circumference
