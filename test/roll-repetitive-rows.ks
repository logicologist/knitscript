pattern main
  row: CO.
  -- Simple case: 4 K's.
  row: K.
  row: K.
  row: K.
  row: K.
  -- Test threshold: the groups of two should be ignored in favor of the larger
  -- group of 4.
  row: P.
  row: P.
  row: K.
  row: K.
  row: P.
  row: P.
  row: K.
  row: K.
  row: P.
  row: P.
  row: K.
  row: K.
  -- Test creating a repeat with an odd number of rows inside.
  row: P.
  row: P.
  row: K.
  row: P.
  row: P.
  row: K.
  row: P.
  row: P.
  row: K.
  row: BO.
end
