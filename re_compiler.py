def Gcode_recompiler(filename):

  #Setting neighborhood threshold to be 0.5
  neighborhood_threshold = 0.5

  extrution = \
    [s for s in g_code_contents if "G1" in s]
  X_in_extrution = \
    [s for s in extrution if "X" in s]

  group = []
  for value in X_in_extrution:
    if (current_X_value-neighborhood_threshold) \
            <= value <= \
       (current_X_value+neighborhood_threshold):
          current_X_value = value
          group.append(value)
    else:
      continue

  X_groups = \
    [x_group
     for x_group in X_groups
     if len(x_group)>=2]

  #Similar methodology for Y

  return groupable_X, groupable_Y
