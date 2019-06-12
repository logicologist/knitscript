pattern upTriangle
  row: SSK, K 5, K2TOG.
  row: P 7.
  row: SSK, K 3, K2TOG.
  row: P 5.
  row: SSK, K 1, K2TOG.
  row: P 3.
end

pattern downTriangle
  row: KFB, K 1, KFB.
  row: P 5.
  row: KFB, K 3, KFB.
  row: P 7.
  row: KFB, K 5, KFB.
  row: P 9.
end

pattern wibbly
  upTriangle.
  downTriangle.
end

pattern downWobbly
  row: KFB, K 1, KFB.
  row: P to end.
  repeat 2
    row: KFB, K to end, KFB.
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

