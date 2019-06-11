-- Common stitch textures

pattern garter
  row: K.
  row: K.
end

pattern stst
  row: K.
  row: P.
end

pattern rib (a, b)
  row: K a, P b.
  row: K b, P a.
end

pattern seed
  row: K, P.
  row: P, K.
end



-- Fancier stitch textures

pattern pineTrees
  row: K, (YO, P 3, SL2TOG_K, K, PSSO 2, P 3, YO, K 9) to last 10,
       YO, P 3, SL2TOG_K, K, PSSO 2, P 3, YO, K.
  row: P to end.
  row: K, (K, YO, P 2, SL2TOG_K, K, PSSO 2, P 2, YO, K 10) to last 10,
       K, YO, P 2, SL2TOG_K, K, PSSO 2, P 2, YO, K 2.
  row: P to end.
  row: K, (K 2, YO, P, SL2TOG_K, K, PSSO 2, P, YO, K 11) to last 10,
       K 2, YO, P, SL2TOG_K, K, PSSO 2, P, YO, K 3.
  row: P to end.
  row: K, (K 3, YO, SL2TOG_K, K, PSSO 2, YO, K 12) to last 10,
       K 3, YO, SL2TOG_K, K, PSSO 2, YO, K 4.
  row: P to end.
  row: K, (K 9, YO, P 3, SL2TOG_K, K, PSSO 2, P 3, YO) to last 10, K 10.
  row: P to end.
  row: K, (K 10, YO, P 2, SL2TOG_K, K, PSSO 2, P 2, YO, K) to last 10, K 10.
  row: P to end.
  row: K, (K 11, YO, P, SL2TOG_K, K, PSSO 2, P, YO, K 2) to last 10, K 10.
  row: P to end.
  row: K, (K 12, YO, SL2TOG_K, K, PSSO 2, YO, K 3) to last 10, K 10.
  row: P to end.
end



-- Library functions

pattern tile (p, n, m)
  repeat m
    p n.
  end
end

pattern pad (p, before, after)
  repeat before
    row: empty.
  end
  p.
  repeat after
    row: empty.
  end
end
