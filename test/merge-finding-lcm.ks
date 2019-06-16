pattern left
  repeat 6
    row: K, K, K, K.
    row: P, P, P, P.
  end
end

pattern right
  repeat 4
    row RS: P 2, P 2.
    row WS: K 2, K 2.
    row RS: K2TOG, YO, K2TOG, YO.
  end
end

pattern main
  row: CO 8.
  left, right.
  row: BO 8.
end

show (main, "Row repeats in a block")
