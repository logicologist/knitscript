using upTriangle, downTriangle from triangles

pattern wibbly
  upTriangle.
  downTriangle.
end

pattern downWobbly
  row: KFB, K 1, KFB.
  row: P to end.
  repeat 2
    row: KFB, K to last 1, KFB.
    row: P to end.
  end
end

pattern upWobbly
  repeat 3
    row: SSK, K to last 2, K2TOG.
    row: P to end.
  end
end

pattern wobbly
  downWobbly.
  upWobbly.
end

pattern wibblyWobbly
  repeat 2
    wibbly, wobbly, wibbly.
  end
end

show (standalone (wibblyWobbly))

