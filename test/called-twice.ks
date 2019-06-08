pattern foo (p)
  p (7).
end

pattern bar (n)
  row: P n.
end

pattern main
  row: CO 5.
  foo (bar (5)).
  row: BO 5.
end
