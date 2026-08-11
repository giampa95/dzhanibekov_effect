model tennis_racket

  // Dzhanibekov effect can be seen by imposing initial rotation in the intermediate inertia axis.
  // In this example, it corresponds to the 1-axis in this example.

  final parameter String cad_path = "modelica://tennis_racket/model/10540_Tennis_racket_V2_L3.obj";

  final parameter Real scale = 0.008 "scale factor for CAD mesh and visualization";
  final parameter Modelica.Units.SI.Mass mass = 0.397901 "mass of the body";

  final parameter Modelica.Units.SI.MomentOfInertia inertia_11 = 0.009676  "11 entry of inertia tensor";
  final parameter Modelica.Units.SI.MomentOfInertia inertia_22 = 0.001526  "22 entry of inertia tensor";
  final parameter Modelica.Units.SI.MomentOfInertia inertia_33 = 0.011190  "33 entry of inertia tensor";
  final parameter Modelica.Units.SI.MomentOfInertia inertia_21 = 0.000002  "21/12 cross entry of inertia tensor";
  final parameter Modelica.Units.SI.MomentOfInertia inertia_31 = 0.000000  "31/13 cross entry of inertia tensor";
  final parameter Modelica.Units.SI.MomentOfInertia inertia_32 = -0.000003 "32/23 cross entry of inertia tensor";

  final parameter Modelica.Units.SI.Position r_cm[3] = {0.000341, 0.084665, 0.004965} "center of mass of the body";
  final parameter Modelica.Units.SI.Position r_0[3] = {0, 0, 0} "initial position";
  final parameter Modelica.Units.SI.Velocity v_0[3] = {0, 5, 0} "initial velocity";
  final parameter Modelica.Units.SI.Angle alpha_0[3] = {0, Modelica.Constants.pi, 0} "initial angle";

  parameter Real omega_0_1_rpm = 60.0   "1-axis initial rotation (intermediate inertia axis)";
  parameter Real omega_0_2_rpm = 5.0    "2-axis initial rotation";
  parameter Real omega_0_3_rpm = 5.0    "3-axis initial rotation";
  
  final parameter Modelica.Units.SI.AngularVelocity omega_0_1_radps 
    = (Modelica.Constants.pi / 30) * omega_0_1_rpm; 
  final parameter Modelica.Units.SI.AngularVelocity omega_0_2_radps 
    = (Modelica.Constants.pi / 30) * omega_0_2_rpm; 
  final parameter Modelica.Units.SI.AngularVelocity omega_0_3_radps 
    = (Modelica.Constants.pi / 30) * omega_0_3_rpm; 
  final parameter Modelica.Units.SI.AngularVelocity omega_0[3] 
    = {omega_0_1_radps, omega_0_2_radps, omega_0_3_radps} "initial rotation";

  inner Modelica.Mechanics.MultiBody.World 
    world(
      g = 0*Modelica.Constants.g_n
      ) annotation(
    Placement(transformation(origin = {50, 10}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Mechanics.MultiBody.Parts.Body 
    body(
      m = mass, 
      I_11 = inertia_11, I_22 = inertia_22, I_33 = inertia_33,
      I_21 = inertia_21, I_31 = inertia_31, I_32 = inertia_32,
      r_CM = r_cm,
      r_0(start = r_0, each fixed = true),
      v_0(start = v_0, each fixed = true), 
      angles_fixed = true,
      angles_start = alpha_0, 
      w_0_fixed = true, 
      w_0_start = omega_0
      ) annotation(
    Placement(transformation(origin = {-30, 10}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));

  Modelica.Mechanics.MultiBody.Visualizers.FixedFrame fixedFrame annotation(
    Placement(transformation(origin = {10, 10}, extent = {{-10, -10}, {10, 10}})));

  Modelica.Mechanics.MultiBody.Visualizers.FixedShape 
    fixedShape(
        length = scale, width = scale, height = scale,
        shapeType = cad_path,
        specularCoefficient=0.1
      ) annotation(
    Placement(transformation(origin = {-20, 40}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));

equation

  connect(body.frame_a, fixedFrame.frame_a) annotation(
    Line(points = {{-20, 10}, {0, 10}}, color = {95, 95, 95}, thickness = 1));

  connect(body.frame_a, fixedShape.frame_a) annotation(
    Line(points = {{-20, 10}, {-20, 30}}, color = {95, 95, 95}, thickness = 1));

annotation(
    uses(Modelica(version = "4.0.0")),
    experiment(StartTime = 0, StopTime = 1.6, Tolerance = 1e-08, Interval = 0.10));

end tennis_racket;
