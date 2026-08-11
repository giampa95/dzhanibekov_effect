# Import bodyprop
from bodyprop import Body

# Body scaling
scale = 0.008

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
body_volume = body.compute_volume()
body_mass = body.compute_mass()
body_com = body.compute_com() 
body_inertia_com = body.compute_inertia()
body_principal_moments = body.compute_principal_moments()
body_principal_axes = body.compute_principal_axes()


# Print some properties/results
print(f"Scale: {scale:.6f}")
print(f"Volume in [m3]: {body_volume:.6f}")
print(f"Mass in [kg]:   {body_mass:.6f}")
print(f"Center of Mass (COM) in [m]:\n"    
      f"   {body_com[0]:.6f}, {body_com[1]:.6f}, {body_com[2]:.6f}")
print("Inertia Matrix in [kg][m2]:\n" 
      f"   {body_inertia_com[0][0]:.6f}, {body_inertia_com[0][1]:.6f}, {body_inertia_com[0][2]:.6f}; \n"
      f"   {body_inertia_com[1][0]:.6f}, {body_inertia_com[1][1]:.6f}, {body_inertia_com[1][2]:.6f}; \n"
      f"   {body_inertia_com[2][0]:.6f}, {body_inertia_com[2][1]:.6f}, {body_inertia_com[2][2]:.6f}.")
print("Principal moments in [kg][m2]:\n" 
      f"   {body_principal_moments[0]}, {body_principal_moments[1]}, {body_principal_moments[2]}")
print("Principal axes:\n" 
      f"   1-axis: {body_principal_axes[0]}; \n"
      f"   2-axis: {body_principal_axes[1]}; \n"
      f"   3-axis: {body_principal_axes[2]};")

