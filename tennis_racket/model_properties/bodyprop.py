import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import trimesh


class Body:
    """Computes physical properties (volume, mass, COM, inertia tensor) for 3D STL/OBJ models,

    supporting uniform, group-level, or object-level material densities.
    """

    def __init__(
        self,
        model: Optional[Union[str, Path]] = None,
        scale: float = 1.0,
        density: float = 1000.0,
        groups_density: Optional[Union[dict, str, Path]] = None,
        objects_density: Optional[Union[dict, str, Path]] = None,
    ):
        self.scale: float = scale
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
    # Loading & Configuration
    # ------------------------------------------------------------------

    def load(
        self,
        model: Union[str, Path],
        scale: Optional[float] = None,
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
            # Attempt parsing via direct OBJ tag parser to preserve exact 'o' and 'g' names
            self.submeshes = self._parse_obj_tags(self.model_path, self.scale)

        if not self.submeshes:
            loaded = trimesh.load(
                str(self.model_path),
                force=("mesh" if ext == ".stl" else None),
                group_material=False,
            )

            if isinstance(loaded, trimesh.Scene):
                for geom_name, mesh_obj in loaded.geometry.items():
                    m = mesh_obj.copy()

                    # Extract target name from metadata ('object' or 'group') before geometry key
                    name = (
                        m.metadata.get("object")
                        or m.metadata.get("group")
                        or m.metadata.get("name")
                        or geom_name
                    )

                    m.apply_scale(self.scale)
                    self._process_and_store_mesh(name, m)

            elif isinstance(loaded, trimesh.Trimesh):
                m = loaded.copy()
                m.apply_scale(self.scale)
                self._process_and_store_mesh("default", m)

    def _process_and_store_mesh(self, name: str, mesh: trimesh.Trimesh) -> None:
        """Validates mesh watertightness, corrects face orientation, and stores submesh."""
        if not mesh.is_watertight:
            print(
                f"Submesh '{name}' is not watertight; mass/volume calculations may be inaccurate."
            )

        if mesh.volume < 0:
            mesh.invert()
            mesh._cache.clear()

        self.submeshes[name] = mesh

    def _parse_obj_tags(
        self, file_path: Path, scale: float
    ) -> Dict[str, trimesh.Trimesh]:
        """Parses OBJ file line-by-line to extract geometries grouped by 'o' (object) or 'g' (group) tags."""
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
                        # Triangulate polygons if needed
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
            sub_v = v_arr[unique_v_idx] * scale
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
        targets = self._filter_submeshes(group=group, obj=object)
        return float(sum(mesh.volume for mesh in targets.values()))

    def compute_mass(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> float:
        targets = self._filter_submeshes(group=group, obj=object)
        total_mass = 0.0
        for name, mesh in targets.items():
            rho = self._get_density_for_key(name)
            total_mass += mesh.volume * rho
        return float(total_mass)

    def compute_com(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> np.ndarray:
        targets = self._filter_submeshes(group=group, obj=object)
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
        targets = self._filter_submeshes(group=group, obj=object)

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

    def compute_principal_axes(self, x=None):
        I = self.compute_inertia(x=x)
        eigenvalues, eigenvectors = np.linalg.eigh(I)
        sort_idx = np.argsort(eigenvalues)
        axes = eigenvectors[:, sort_idx]

        if np.linalg.det(axes) < 0:
            axes[:, 2] *= -1

        return axes

    def compute_principal_moments(self, x=None):
        I = self.compute_inertia(x=x)
        eigenvalues = np.linalg.eigvalsh(I)
        return np.sort(eigenvalues)

    def compute_all(
        self, group: Optional[str] = None, object: Optional[str] = None
    ) -> dict:
        return {
            "volume": self.compute_volume(group=group, object=object),
            "mass": self.compute_mass(group=group, object=object),
            "com": self.compute_com(group=group, object=object),
            "inertia": self.compute_inertia(group=group, object=object),
        }