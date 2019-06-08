pattern foo (a, b)
  row: K a, P b.
end

pattern main
  row: CO 3.
  foo (2, 3, 4).
  row: BO 3.
end
