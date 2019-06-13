pattern downTriangle
  row: KFB, K 1, KFB.
  row: P 5.
  row: KFB, K 3, KFB.
  row: P 7.
  row: KFB, K 5, KFB.
  row: P 9.
end

pattern main
  standalone (downTriangle).
end

show (main)