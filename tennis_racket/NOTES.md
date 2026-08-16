Some notes.

---------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------

3D CAD file avaiable at https://free3d.com/3d-model/tennis-racket-v3--693257.html

---------------------------------------------------------------------------------------------------------------

Standard adult tennis rackets measure 68.6-73.6 [cm] in length and about 25-28 [cm] in width across the head. 
The weight is 0.250 - 0.350 [kg]. The composite material used has a density of 1500 - 1800 [kg] per [m3].
Considering the CAD scale equal to 0.01, the lenght measures 68.6 [cm] in lenght and about 30 [cm] in width.
However, considering a body density of 1500 [kg] per [m3], the weight is about 0.7 [kg].

---------------------------------------------------------------------------------------------------------------

Note also that the CAD include strings.
For these ones,  a density higher than the expected one, since the same density is imposed everywhere. 
However, the strings has small volume, therefore we assume their mass negligible.

---------------------------------------------------------------------------------------------------------------

Note that the "axis y" and "axis z" are inverted between Modelica bench and Python script.

---------------------------------------------------------------------------------------------------------------

In Modelica, it seems that Modelica has issues scaling-down the object (from [m] to [cm]).
Since object appears bigger, axes lenghts appear smaller.
This aspect on scaling the object must be investigated.
If a solution will not be found, a possible workaround is to generate a scaled object.

---------------------------------------------------------------------------------------------------------------

Results of Python scripts are attached below.
Cartesian bounding limits and sizes in [m]:
   1: min: -1.514170e-01  max: 1.521280e-01  size: 3.035450e-01
   2: min: -2.407400e-01  max: 4.460130e-01  size: 6.867530e-01
   3: min: -8.660000e-03  max: 2.061800e-02  size: 2.927800e-02
Volume in [m3]: 5.181008e-04
Mass in [kg]:   7.771512e-01
Center of Mass (COM) in [m]:
   4.263154e-04, 1.058315e-01, 6.205808e-03
Inertia Matrix in [kg][m2]:
   2.953002e-02, 5.636889e-06, 3.073764e-08;
   5.636889e-06, 4.655690e-03, -9.778107e-06;
   3.073764e-08, -9.778107e-06, 3.414998e-02.

---------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------
