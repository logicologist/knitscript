pattern main
  row: CO 12.
  pad (fill (rib (2, 2), 4, 8), 0, 4),
    pad (fill (slippedWaves, 8, 4), 0, 8),
    pad (fill (seed, 4, 4), 4, 4),
    pad (fill (garter, 8, 4), 8, 0),
    pad (fill (stripes, 4, 8), 4, 0).
  row: BO to end.
end

show (main)

