pattern foo
  row: K, K, (P, K, K) 2, K.
end

pattern main
  row: CO 9.
  reflect (foo).
  row: BO 9.
end
