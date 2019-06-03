pattern p1
  row: K a.
end

pattern p2 (a)
  p1.
end

pattern main
  row: CO 7.
  p2 (7).
  row: BO 7.
end

