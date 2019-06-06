pattern seed
  row: K, P.
  row: P, K.
end

pattern tile (p, n, m)
  repeat m
    p n.
  end
end

pattern main
  row: CO 6.
  tile (seed, 3, 3).
  row: BO 6.
end

