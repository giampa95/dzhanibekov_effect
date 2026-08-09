model rectangular_prism
  
  // Dzhanibekov effect can be seen by imposing initial rotation in the 2-axis.
  
  parameter Real density = 1;
  parameter Real lenght_1 = 1;
  parameter Real lenght_2 = 3;
  parameter Real lenght_3 = 12;
  
  final parameter Real mass = density*lenght_1*lenght_2*lenght_3 "mass of the body";
  final parameter Real inertia_11 = (1/12)*mass*(lenght_2^2 + lenght_3^2) "1-axis inertia of the body";
  final parameter Real inertia_22 = (1/12)*mass*(lenght_1^2 + lenght_3^2) "2-axis inertia of the body";
  final parameter Real inertia_33 = (1/12)*mass*(lenght_1^2 + lenght_2^2) "3-axis inertia of the body";
  final parameter Real r_cm[3] = {0, 0, 0} "center of mass of the body";
  final parameter Real r_0[3] = { 0, 0, 0} "initial position";
  final parameter Real v_0[3] = { 0, 0, 0} "initial velocity";
  final parameter Real alpha_0[3] = { 0, 0, 0} "initial angle";
  
  parameter Real omega_0_1_rpm = 1e-3 "1-axis initial rotation";
  parameter Real omega_0_2_rpm = 30   "2-axis initial rotation";
  parameter Real omega_0_3_rpm = 1e-3 "3-axis initial rotation";
  final parameter Real omega_0_1_radps = (Modelica.Constants.pi / 30) * omega_0_1_rpm; 
  final parameter Real omega_0_2_radps = (Modelica.Constants.pi / 30) * omega_0_2_rpm; 
  final parameter Real omega_0_3_radps = (Modelica.Constants.pi / 30) * omega_0_3_rpm; 
  final parameter Real omega_0[3] = { omega_0_1_radps, omega_0_2_radps, omega_0_3_radps} "initial rotation";
  
  inner Modelica.Mechanics.MultiBody.World 
    world(
      g = 0
      ) annotation(
    Placement(transformation(origin = {50, 10}, extent = {{-10, -10}, {10, 10}})));
  
  Modelica.Mechanics.MultiBody.Parts.Body 
    body(
      m = mass, 
      I_11 = inertia_11, I_22 = inertia_22, I_33 = inertia_33, 
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
      length = lenght_1, width = lenght_2, height = lenght_3,
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
    experiment(StartTime = 0, StopTime = 60, Tolerance = 1e-06, Interval = 0.10));

end rectangular_prism;
