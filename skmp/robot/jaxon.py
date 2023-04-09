from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from robot_descriptions.jaxon_description import URDF_PATH as JAXON_URDF_PATH
from skrobot.coordinates import CascadedCoords
from skrobot.coordinates.math import rotation_matrix, rpy_angle
from skrobot.models.urdf import RobotModelFromURDF
from tinyfk import BaseType, RobotModel

from skmp.constraint import BoxConst
from skmp.kinematics import ArticulatedEndEffectorKinematicsMap


class Jaxon(RobotModelFromURDF):
    rarm_end_coords: CascadedCoords
    larm_end_coords: CascadedCoords
    rleg_end_coords: CascadedCoords
    lleg_end_coords: CascadedCoords

    def __init__(self):
        super().__init__(urdf_file=JAXON_URDF_PATH)
        matrix = rotation_matrix(np.pi * 0.5, [0, 0, 1.0])

        self.rarm_end_coords = CascadedCoords(self.RARM_LINK7, name="rarm_end_coords")
        self.rarm_end_coords.translate([0, 0, -0.220])
        self.rarm_end_coords.rotate_with_matrix(matrix, wrt="local")

        self.larm_end_coords = CascadedCoords(self.LARM_LINK7, name="larm_end_coords")
        self.larm_end_coords.translate([0, 0, -0.220])
        self.larm_end_coords.rotate_with_matrix(matrix, wrt="local")

        self.rleg_end_coords = CascadedCoords(self.RLEG_LINK5, name="rleg_end_coords")
        self.rleg_end_coords.translate([0, 0, -0.1])

        self.lleg_end_coords = CascadedCoords(self.LLEG_LINK5, name="lleg_end_coords")
        self.lleg_end_coords.translate([0, 0, -0.1])

    def default_urdf_path(self):
        return JAXON_URDF_PATH


@dataclass
class JaxonConfig:
    @classmethod
    def urdf_path(cls) -> Path:
        return Path(JAXON_URDF_PATH)

    @staticmethod
    def add_end_coords(robot_model: RobotModel) -> None:
        rarm_id, larm_id = robot_model.get_link_ids(["RARM_LINK7", "LARM_LINK7"])
        matrix = rotation_matrix(np.pi * 0.5, [0, 0, 1.0])
        rpy = np.flip(rpy_angle(matrix)[0])
        robot_model.add_new_link("rarm_end_coords", rarm_id, [0, 0, -0.220], rotation=rpy)
        robot_model.add_new_link("larm_end_coords", larm_id, [0, 0, -0.220], rotation=rpy)

        rleg_id, lleg_id = robot_model.get_link_ids(["RLEG_LINK5", "LLEG_LINK5"])
        robot_model.add_new_link("rleg_end_coords", rleg_id, [0, 0, -0.1])
        robot_model.add_new_link("lleg_end_coords", lleg_id, [0, 0, -0.1])

    def _get_control_joint_names(self) -> List[str]:
        joint_names = []
        for i in range(8):
            joint_names.append("RARM_JOINT{}".format(i))
            joint_names.append("LARM_JOINT{}".format(i))
        for i in range(6):
            joint_names.append("RLEG_JOINT{}".format(i))
            joint_names.append("LLEG_JOINT{}".format(i))
        for i in range(3):
            joint_names.append("CHEST_JOINT{}".format(i))
        return joint_names

    def _get_endeffector_names(self) -> List[str]:
        return ["rleg_end_coords", "lleg_end_coords", "rarm_end_coords", "larm_end_coords"]
        # return ["rleg_end_coords", "lleg_end_coords"]

    def get_endeffector_kin(self):
        kinmap = ArticulatedEndEffectorKinematicsMap(
            self.urdf_path(),
            self._get_control_joint_names(),
            self._get_endeffector_names(),
            base_type=BaseType.FLOATING,
            fksolver_init_hook=self.add_end_coords,
        )
        return kinmap

    def get_box_const(self) -> BoxConst:
        base_bounds = np.array([-1.0, -1.0, -2.0, -1.0, -1.0, -1.0]), np.array(
            [1.0, 1.0, 2.0, 1.0, 1.0, 1.0]
        )
        bounds = BoxConst.from_urdf(
            self.urdf_path(), self._get_control_joint_names(), base_bounds=base_bounds
        )
        return bounds
