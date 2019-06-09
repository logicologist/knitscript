pattern a
  row: CO 2.
  row: K, P.
  row: BO 2.
end

pattern b
  row: CO 2.
  row: K, P.
  row: P, K.
  row: BO 2.
end

pattern main
  b, a.
end

show (main, "Patterns with different numbers of rows in a block")
