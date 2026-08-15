import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union
import numpy as np
import trimesh

# Type alias for scale input
ScaleType = Union[float, int, Sequence[float], np.ndarray]


class Body:
    """Computes physical properties (volume, mass, COM, inertia tensor) for 3D STL/OBJ models,

    supporting uniform, group-level, or object-level material densities,
    as well as dynamic uniform or directional anisotropic scaling.
    """

    def __init__(
        self,
        model: Optional[Union[str, Path]] = None,
        scale: ScaleType = 1.0,
        density: float = 1000.0,
        groups_density: Optional[Union[dict, str, Path]] = None,
        objects_density: Optional[Union[dict, str, Path]] = None,
    ):
        self._scale: Union[float, np.ndarray] = 1.0
        self.scale = scale  # Uses setter validation
        self.density: float = density
        self.groups_density: Dict[str, float] = self._parse_density_input(
            groups_density
        )
        self.objects_density: Dict[str, float] = self._parse_density_input(
            objects_density
        )
        self.submeshes: Dict[str, trimesh.Trimesh] = {}
        self.model_path: Optional[Path] = None

        if model is not None:
            self.load(
                model=model,
                scale=scale,
                density=density,
                groups_density=groups_density,
                objects_density=objects_density,
            )

    # ------------------------------------------------------------------
    # Properties & Helper Validation
    # ------------------------------------------------------------------

    @property
    def scale(self) -> Union[float, np.ndarray]:
        """Returns the current scale setting."""
        return self._scale

    @scale.setter
    def scale(self, value: ScaleType) -> None:
        """Sets and validates the scale setting."""
        self._scale = self._validate_scale(value)

    def _validate_scale(self, scale: ScaleType) -> Union[float, np.ndarray]:
        """Validates scale input to be either a positive float or a 3-element sequence [sx, sy, sz]."""
        if isinstance(scale, (int, float, np.number)):
            val = float(scale)
            if val <= 0:
                raise ValueError(f"Scale must be positive, got {val}")
            return val

        try:
            arr = np.asarray(scale, dtype=np.float64)
            if arr.ndim == 0:
                val = float(arr)
                if val <= 0:
                    raise ValueError(f"Scale must be positive, got {val}")
                return val
            elif arr.shape == (3,):
                if np.any(arr <= 0):
                    raise ValueError(
                        f"All scale components must be positive, got {arr}"
                    )
                return arr
        except Exception as e:
            if isinstance(e, ValueError):
                raise e

        raise ValueError(
            f"Invalid scale value '{scale}'. Expected a positive float or a 3-element sequence [scale_x, scale_y, scale_z]."
        )

    # ------------------------------------------------------------------
    # Loading & Configuration
    # ------------------------------------------------------------------

    def load(
        self,
        model: Union[str, Path],
        scale: Optional[ScaleType] = None,
        density: Optional[float] = None,
        groups_density: Optional[Union[dict, str, Path]] = None,
        objects_density: Optional[Union[dict, str, Path]] = None,
    ) -> None:
        """Load or reload a mesh model file and set physical attributes."""
        if scale is not None:
            self.scale = scale
        if density is not None:
            self.density = density
        if groups_density is not None:
            self.groups_density = self._parse_density_input(groups_density)
        if objects_density is not None:
            self.objects_density = self._parse_density_input(objects_density)

        self.model_path = Path(model)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"File not found: {self.model_path}")

        self.submeshes = {}
        ext = self.model_path.suffix.lower()

        if ext == ".obj":
            # Parsing via direct OBJ tag parser to preserve exact 'o' and 'g' names
            self.submeshes = self._parse_obj_tags(self.model_path)

        if not self.submeshes:
            loaded = trimesh.load(
                str(self.model_path),
                force=("mesh" if ext == ".stl" else None),
                group_material=False,
            )

            if isinstance(loaded, trimesh.Scene):
                for geom_name, mesh_obj in loaded.geometry.items():
                    m = mesh_obj.copy()

                    name = (
                        m.metadata.get("object")
                        or m.metadata.get("group")
                        or m.metadata.get("name")
                        or geom_name
                    )

                    # Store original unscaled mesh
                    self._process_and_store_mesh(name, m)

            elif isinstance(loaded, trimesh.Trimesh):
                m = loaded.copy()
                # Store original unscaled mesh
                self._process_and_store_mesh("default", m)

    def _process_and_store_mesh(self, name: str, mesh: trimesh.Trimesh) -> None:
        """Validates mesh watertightness, corrects face orientation, and stores original unscaled submesh."""
        if not mesh.is_watertight:
            print(
                f"Submesh '{name}' is not watertight; mass/volume calculations may be inaccurate."
            )

        if mesh.volume < 0:
            mesh.invert()
            mesh._cache.clear()

        self.submeshes[name] = mesh

    def _parse_obj_tags(self, file_path: Path) -> Dict[str, trimesh.Trimesh]:
        """Parses OBJ file line-by-line to extract original unscaled geometries grouped by 'o' or 'g' tags."""
        vertices = []
        submesh_faces: Dict[str, list] = {}
        current_tag = "default"

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                prefix = parts[0].lower()

                if prefix in ("o", "g"):
                    if len(parts) > 1:
                        current_tag = parts[1]
                elif prefix == "v":
                    vertices.append(
                        [float(parts[1]), float(parts[2]), float(parts[3])]
                    )
                elif prefix == "f":
                    face_v = []
                    for vert in parts[1:]:
                        idx = int(vert.split("/")[0])
                        idx = idx - 1 if idx > 0 else len(vertices) + idx
                        face_v.append(idx)

                    if len(face_v) >= 3:
                        for i in range(1, len(face_v) - 1):
                            submesh_faces.setdefault(current_tag, []).append(
                                [face_v[0], face_v[i], face_v[i + 1]]
                            )

        if not submesh_faces or not vertices:
            return {}

        v_arr = np.array(vertices, dtype=np.float64)
        parsed_submeshes = {}

        for tag, faces in submesh_faces.items():
            f_arr = np.array(faces, dtype=np.int64)
            unique_v_idx, reindexed_f = np.unique(f_arr, return_inverse=True)
            sub_v = v_arr[unique_v_idx]  # Unscaled vertices
            sub_f = reindexed_f.reshape(f_arr.shape)

            m = trimesh.Trimesh(vertices=sub_v, faces=sub_f, process=True)

            if not m.is_watertight:
                print(
                    f"Submesh '{tag}' is not watertight; mass/volume calculations may be inaccurate."
                )
            if m.volume < 0:
                m.invert()
                m._cache.clear()

            parsed_submeshes[tag] = m

        return parsed_submeshes

    def _parse_density_input(
        self, density_input: Optional[Union[dict, str, Path]]
    ) -> Dict[str, float]:
        if density_input is None:
            return {}
        if isinstance(density_input, dict):
            return {k: float(v) for k, v in density_input.items()}
        if isinstance(density_input, (str, Path)):
            p = Path(density_input)
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    return {k: float(v) for k, v in json.load(f).items()}
            return {
                k: float(v) for k, v in json.loads(str(density_input)).items()
            }
        return {}

    def _get_density_for_key(self, name: str) -> float:
        if name in self.objects_density:
            return self.objects_density[name]
        if name in self.groups_density:
            return self.groups_density[name]
        return self.density

    def _filter_submeshes(
        self, group: Optional[str] = None, obj: Optional[str] = None
    ) -> Dict[str, trimesh.Trimesh]:
        target = group or obj
        if target is not None:
            if target not in self.submeshes:
                raise KeyError(
                    f"Group/Object '{target}' not found. Available: {list(self.submeshes.keys())}"
                )
            return {target: self.submeshes[target]}
        return self.submeshes

    def _get_scaled_submesh(self, name: str) -> trimesh.Trimesh:
        """Returns a copy of the submesh scaled according to current self.scale."""
        mesh = self.submeshes[name].copy()

        # Optimization: skip scaling if scale is identity
        if isinstance(self.scale, (int, float, np.number)) and float(self.scale) == 1.0:
            return mesh
        if isinstance(self.scale, np.ndarray) and np.array_equal(self.scale, [1.0, 1.0, 1.0]):
            return mesh

        mesh.apply_scale(self.scale)
        return mesh

    def _get_scaled_targets(
        self, group: Optional[str] = None, obj: Optional[str] = None
    ) -> Dict[str, trimesh.Trimesh]:
        """Filters submeshes and returns copies scaled to current scale setting."""
        unscaled_targets = self._filter_submeshes(group=group, obj=obj)
        return {name: self._get_scaled_submesh(name) for name in unscaled_targets}

    # ------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------

    def list_groups(self) -> List[str]:
        return list(self.submeshes.keys())

    def list_objects(self) -> List[str]:
        return list(self.submeshes.keys())

    # ------------------------------------------------------------------
    # Property Computations
    # ------------------------------------------------------------------

    def compute_volume(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> float:
        targets = self._get_scaled_targets(group=group, obj=object)
        return float(sum(mesh.volume for mesh in targets.values()))

    def compute_mass(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> float:
        targets = self._get_scaled_targets(group=group, obj=object)
        total_mass = 0.0
        for name, mesh in targets.items():
            rho = self._get_density_for_key(name)
            total_mass += mesh.volume * rho
        return float(total_mass)

    def compute_com(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> np.ndarray:
        targets = self._get_scaled_targets(group=group, obj=object)
        total_mass = 0.0
        weighted_com = np.zeros(3)

        for name, mesh in targets.items():
            rho = self._get_density_for_key(name)
            m = mesh.volume * rho
            total_mass += m
            weighted_com += m * mesh.center_mass

        if total_mass == 0.0:
            return np.zeros(3)
        return weighted_com / total_mass

    def compute_inertia(
        self,
        x: Optional[Union[np.ndarray, list, tuple]] = None,
        group: Optional[str] = None,
        object: Optional[str] = None,
    ) -> np.ndarray:
        targets = self._get_scaled_targets(group=group, obj=object)

        ref_point = (
            np.array(x, dtype=float)
            if x is not None
            else self.compute_com(group=group, object=object)
        )
        I_total = np.zeros((3, 3))

        for name, mesh in targets.items():
            rho = self._get_density_for_key(name)
            m = mesh.volume * rho
            I_mesh_com = mesh.moment_inertia * rho

            d = mesh.center_mass - ref_point
            dx, dy, dz = d
            J = m * np.array(
                [
                    [dy**2 + dz**2, -dx * dy, -dx * dz],
                    [-dx * dy, dx**2 + dz**2, -dy * dz],
                    [-dx * dz, -dy * dz, dx**2 + dy**2],
                ]
            )

            I_total += I_mesh_com + J

        return 0.5 * (I_total + I_total.T)

    def compute_principal_inertia(
        self,
        x: Optional[Union[np.ndarray, list, tuple]] = None,
        group: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Dict[str, Union[float, np.ndarray]]]:
        """Computes principal moments of inertia and their associated normalized principal axes.

        Returns a list of dictionaries containing paired moments and normalized column vectors,
        sorted by ascending moment magnitude.
        """
        I = self.compute_inertia(x=x, group=group, object=object)
        eigenvalues, eigenvectors = np.linalg.eigh(I)

        # Sort by moment size
        sort_idx = np.argsort(eigenvalues)
        moments = eigenvalues[sort_idx]
        axes = eigenvectors[:, sort_idx]

        # Preserve right-handed coordinate frame
        if np.linalg.det(axes) < 0:
            axes[:, 2] *= -1

        # Explicitly normalize each principal axis vector
        axes = axes / np.linalg.norm(axes, axis=0)

        return [
            {"moment": float(moments[i]), "axis": axes[:, i]}
            for i in range(3)
        ]


    def compute_bounds(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> List[Dict[str, float]]:
        """Computes min, max, and bounding size (max - min) for each Cartesian direction (X, Y, Z).

        Returns a list of 3 dictionaries (index 0=X, 1=Y, 2=Z) containing:
        - 'min': minimum coordinate value
        - 'max': maximum coordinate value
        - 'size': bounding length (max - min)
        """
        targets = self._get_scaled_targets(group=group, obj=object)
        if not targets:
            return [{"min": 0.0, "max": 0.0, "size": 0.0} for _ in range(3)]

        mins = np.array([mesh.bounds[0] for mesh in targets.values()])
        maxs = np.array([mesh.bounds[1] for mesh in targets.values()])

        overall_min = np.min(mins, axis=0)
        overall_max = np.max(maxs, axis=0)
        overall_size = overall_max - overall_min

        return [
            {
                "min": float(overall_min[i]),
                "max": float(overall_max[i]),
                "size": float(overall_size[i]),
            }
            for i in range(3)
        ]