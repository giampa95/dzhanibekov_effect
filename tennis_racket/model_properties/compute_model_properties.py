# Import bodyprop
from bodyprop import Body

# Body scaling
scale = 0.01

# Body definition
body = Body(
    model="../model/10540_Tennis_racket_V2_L3.obj",
    scale=scale,           
    density=1500.0         # body density
)

# Compute list of objects/groups in the model
list_objects = body.list_objects()
list_groups = body.list_groups()

# Compute properties for the body
body_bounds = body.compute_bounds()
body_volume = body.compute_volume()
body_mass = body.compute_mass()
body_com = body.compute_com() 
body_inertia_com = body.compute_inertia()


# Print some properties/results
print(f"")
print(f"Scale: {scale:.6e}")
print("Cartesian bounding limits and sizes in [m]:\n"
      f"   1: min: {body_bounds[0]['min']:.6e}  max: {body_bounds[0]['max']:.6e}  size: {body_bounds[0]['size']:.6e}\n"
      f"   2: min: {body_bounds[1]['min']:.6e}  max: {body_bounds[1]['max']:.6e}  size: {body_bounds[1]['size']:.6e}\n"
      f"   3: min: {body_bounds[2]['min']:.6e}  max: {body_bounds[2]['max']:.6e}  size: {body_bounds[2]['size']:.6e}")
print(f"Volume in [m3]: {body_volume:.6e}")
print(f"Mass in [kg]:   {body_mass:.6e}")
print(f"Center of Mass (COM) in [m]:\n"    
      f"   {body_com[0]:.6e}, {body_com[1]:.6e}, {body_com[2]:.6e}")
print("Inertia Matrix in [kg][m2]:\n" 
      f"   {body_inertia_com[0, 0]:.6e}, {body_inertia_com[0, 1]:.6e}, {body_inertia_com[0, 2]:.6e}; \n"
      f"   {body_inertia_com[1, 0]:.6e}, {body_inertia_com[1, 1]:.6e}, {body_inertia_com[1, 2]:.6e}; \n"
      f"   {body_inertia_com[2, 0]:.6e}, {body_inertia_com[2, 1]:.6e}, {body_inertia_com[2, 2]:.6e}.")
