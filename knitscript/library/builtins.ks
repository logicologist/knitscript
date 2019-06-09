
-- Common stitch textures

pattern garter
  row: K.
end

pattern stst
  row: K.
  row: P.
end

pattern rib (a,b)
  row: K a, P b.
  row: K b, P a.
end

pattern seed
  row: K, P.
  row: P, K.
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
