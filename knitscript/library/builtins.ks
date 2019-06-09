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
