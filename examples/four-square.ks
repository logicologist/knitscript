pattern squares
  tile(slippedWaves, 4, 2), tile(stst, 8, 4).
  tile(seed, 4, 4), tile(rib(1,1), 4, 4).
end

pattern fourSquare
  row: CO 20.
  garterBorder(squares, 4, 2).
  row: BO to end.
end

show (fourSquare)

