pattern left
  row: K 5.
  row: P 5.
  row: K to end.
end

pattern right
  row: P, K.
  row: K 2.
  row: P 2.
end

pattern main
  row: CO 9.
  left, right, right.
  row: BO 9.
end

show (main, "Expanding stitch repeat in a block")
