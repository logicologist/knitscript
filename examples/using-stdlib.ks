using garter, stst, rib, seed, tile from stdlib

pattern main
  row: CO 12.
  tile (garter, 12, 4).
  tile (garter, 2, 4), tile (stst, 8, 2), tile (garter, 2, 4).
  tile (garter, 12, 2).
  row: BO 12.
end
