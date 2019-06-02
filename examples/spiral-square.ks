pattern topLeft
  row RS: K.
  row WS: K.
end

pattern topRight
  row RS: P, P.
end

pattern middle
  row WS: YO.
end

pattern bottomLeft
  row RS: P, P.
end

pattern bottomRight
  row WS: K.
  row RS: K.
end

pattern pad (p, above, below)
  repeat above
    row: empty.
  end
  p.
  repeat below
    row: empty.
  end
end

pattern main
  pad (topLeft, 0, 1),
  pad (topRight, 0, 2),
  pad (middle, 1, 1),
  pad (bottomLeft, 2, 0),
  pad (bottomRight, 1, 0).
end
