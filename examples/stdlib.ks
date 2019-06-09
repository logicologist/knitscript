
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



-- Tiling a pattern a certain number of times

pattern tile (p, n, m)
  repeat m
    p n.
  end
end

